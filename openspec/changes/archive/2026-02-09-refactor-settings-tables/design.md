## Context

The current settings system uses a single polymorphic `settings` table with a `setting_type` discriminator and generic JSON `config` column. This was likely chosen for flexibility but has created maintenance and reliability issues:

- No database-level validation or constraints
- Inefficient queries (always filtering by `setting_type`)
- Schema ambiguity (different types need different fields)
- Encryption/decryption happens on every read/write
- Several bugs: HTTP method mismatch, silent encryption key generation, stubbed tool testing

The system currently stores three types: LLM providers (OpenAI, Anthropic, Azure, Custom), external tools (ELK, GitLab, K8s, Neo4j), and database configs (unused in UI per CLAUDE.md).

## Goals / Non-Goals

**Goals:**
- Dedicated tables with typed columns for each setting type
- Database-level constraints (unique names, single default provider)
- Fix critical bugs (HTTP method, encryption key, tool testing)
- Zero-downtime migration with data preservation
- Maintain API backward compatibility (frontend unchanged)

**Non-Goals:**
- Changing the UI or user-facing behavior
- Adding new features beyond bug fixes
- Modifying the encryption algorithm itself
- Supporting rollback to old schema (one-way migration)

## Decisions

### 1. Separate Tables vs. Single Table Inheritance

**Decision**: Create three dedicated tables (`llm_providers`, `external_tools`, `database_configs`)

**Rationale**:
- Each type has distinct fields (e.g., Azure needs `deployment`, tools need `last_test_status`)
- Database can enforce type-specific constraints
- Queries are simpler and faster (no discriminator filtering)
- Schema changes to one type don't affect others

**Alternative considered**: Keep single table with better JSON schema validation
- Rejected: Still can't enforce constraints like "only one default provider" at DB level
- Rejected: JSON queries are slower and less maintainable

### 2. Repository Pattern

**Decision**: Keep single `SettingRepository` but add type-specific methods

**Rationale**:
- Minimizes code changes (existing code uses `SettingRepository`)
- Encryption logic stays centralized
- Can add `get_llm_provider()`, `get_external_tool()` methods that return typed models

**Alternative considered**: Create `LLMProviderRepository`, `ExternalToolRepository`, etc.
- Rejected: More boilerplate, duplicated encryption logic
- Rejected: Breaks existing code that imports `SettingRepository`

### 3. Migration Strategy

**Decision**: Blue-green migration with data copy and validation

**Steps**:
1. Create new tables alongside old `settings` table
2. Copy data from `settings` to new tables with validation
3. Update repository to read from new tables
4. Deploy application (reads from new tables, old table untouched)
5. After validation period, drop old `settings` table

**Rationale**:
- Zero downtime (new tables created before app restart)
- Rollback possible (keep old table until validated)
- Data validation happens during migration (catch config errors early)

**Alternative considered**: In-place ALTER TABLE
- Rejected: Can't split one table into three with ALTER
- Rejected: No rollback path if migration fails

### 4. Encryption Key Management

**Decision**: Fail fast in production, loud warning in development

**Rationale**:
- Production: Data loss from key change is catastrophic → fail immediately
- Development: Auto-generate for convenience but warn loudly
- Check `ENVIRONMENT` env var to determine mode

**Alternative considered**: Always require key
- Rejected: Hurts developer experience (extra setup step)
- Rejected: Current behavior (silent generation) is worse than loud warning

### 5. Config Validation

**Decision**: Pydantic discriminated union models per provider type

```python
class OpenAIConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    api_key: str
    base_url: Optional[str] = None
    models: List[str]

class AzureConfig(BaseModel):
    provider: Literal["azure"] = "azure"
    api_key: str
    base_url: str  # Required
    deployment: str  # Required for Azure
    models: List[str]

LLMProviderConfig = OpenAIConfig | AnthropicConfig | AzureConfig | CustomConfig
```

**Rationale**:
- Catches config errors at API boundary (before database)
- Type-safe validation (Azure requires `deployment`, OpenAI doesn't)
- Clear error messages for users

**Alternative considered**: JSON Schema validation
- Rejected: Less type-safe, harder to maintain
- Rejected: Pydantic integrates better with FastAPI

### 6. Default Provider Auto-Promotion

**Decision**: When deleting default provider, auto-promote first enabled provider

**Rationale**:
- System should always have a default if providers exist
- Better UX than forcing manual selection
- Predictable behavior (first enabled = oldest/most stable)

**Alternative considered**: Require manual default selection before delete
- Rejected: Poor UX (extra step)
- Rejected: System could end up with no default

### 7. Tool Connection Testing

**Decision**: Simple HTTP GET with 5-second timeout, store results in DB

**Rationale**:
- Most tools expose HTTP endpoints (ELK, GitLab, K8s API, Neo4j)
- 5 seconds balances responsiveness vs. network latency
- Storing `last_test_at` and `last_test_status` enables monitoring

**Alternative considered**: Tool-specific health checks (e.g., Neo4j Bolt protocol)
- Rejected: Too complex for initial implementation
- Future: Can add tool-specific checks later

## Risks / Trade-offs

**[Risk]** Migration fails mid-way, leaving inconsistent state
→ **Mitigation**: Run migration in transaction, validate all data before commit, keep old table for rollback

**[Risk]** Encrypted data becomes unreadable if key changes
→ **Mitigation**: Fail fast in production (won't start without key), document key backup in deployment guide

**[Risk]** Auto-promotion picks wrong provider as default
→ **Mitigation**: Log promotion clearly, allow manual override immediately after

**[Trade-off]** Separate tables = more schema files to maintain
→ **Accepted**: Type safety and query performance worth the maintenance cost

**[Trade-off]** One-way migration (can't rollback to old schema)
→ **Accepted**: Keep old table for data recovery, but app won't support old schema

**[Risk]** Frontend breaks if API response format changes
→ **Mitigation**: Keep response format identical (repository returns same structure)

## Migration Plan

### Pre-deployment

1. **Backup database**: Full backup before migration
2. **Test migration script**: Run on staging with production data copy
3. **Validate encryption key**: Ensure `ENCRYPTION_KEY` set in production env

### Deployment Steps

1. **Create new tables** (via Alembic migration):
   ```sql
   CREATE TABLE llm_providers (...);
   CREATE TABLE external_tools (...);
   CREATE TABLE database_configs (...);
   ```

2. **Migrate data** (in transaction):
   ```python
   # Copy settings where setting_type='llm_provider'
   # Validate each config with Pydantic
   # Insert into llm_providers table
   ```

3. **Deploy application**: New code reads from new tables

4. **Validation period** (24-48 hours):
   - Monitor logs for errors
   - Verify all settings accessible
   - Test CRUD operations

5. **Cleanup**: Drop old `settings` table after validation

### Rollback Strategy

If issues found during validation:
1. Revert application deployment (old code reads from `settings` table)
2. Old table still intact (not dropped yet)
3. Investigate and fix migration script
4. Retry deployment

**Note**: After old table dropped, rollback requires restoring from backup

## Open Questions

1. **Should we add database indexes?**
   - `llm_providers.is_default` (for finding default quickly)
   - `external_tools.tool_type` (for filtering by type)
   - Decision: Yes, add in migration

2. **How to handle concurrent default provider changes?**
   - Two admins set different providers as default simultaneously
   - Decision: Use database constraint + last-write-wins

3. **Should tool testing be async?**
   - Current design: Synchronous HTTP request (blocks API call)
   - Alternative: Queue test in background, return immediately
   - Decision: Start with sync, add async if users complain about latency
