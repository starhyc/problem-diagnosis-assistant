## Context

Current state: LLM providers and database configurations are hardcoded in environment variables (.env file), requiring service restarts for any changes. The Settings page has unused features (redline rules, masking rules) and lacks core configuration capabilities.

Constraints:
- Must maintain backward compatibility during migration (first startup auto-migrates env vars to DB)
- Encryption key must be stored separately from database
- All configuration changes must take effect immediately without restart
- Admin-only access required for all settings operations

## Goals / Non-Goals

**Goals:**
- Enable runtime LLM provider management (add/edit/delete providers, test connections, discover models)
- Enable runtime database configuration management
- Encrypt sensitive data (API keys, passwords) at rest
- Hot-reload configuration changes in llm_factory without restart
- Simplify Settings UI by removing unused features

**Non-Goals:**
- Multi-tenancy (single system-wide configuration)
- Configuration versioning or audit logs (future enhancement)
- Automatic failover testing (manual testing only)
- Migration of existing diagnosis data

## Decisions

### 1. Encryption Strategy: Fernet (Symmetric)

**Decision:** Use `cryptography.fernet.Fernet` for encrypting API keys and passwords.

**Rationale:**
- Symmetric encryption sufficient (no key sharing needed)
- Fernet provides authenticated encryption (prevents tampering)
- Simple API, built-in key rotation support
- Standard Python library

**Alternatives considered:**
- Asymmetric (RSA): Overkill for single-system use case
- AES-GCM directly: More complex, Fernet wraps this properly

**Implementation:**
- Encryption key stored in `ENCRYPTION_KEY` env var (32-byte base64)
- Auto-generate key on first startup if missing
- Encrypt before DB write, decrypt after DB read
- Store encrypted data as base64 string in `config` JSON field

### 2. Hot-Reload Mechanism: Singleton Invalidation

**Decision:** LLMFactory reloads providers from database on each `create_llm()` call, with optional caching.

**Rationale:**
- Simple implementation (no complex pub/sub needed)
- Acceptable performance (DB query cached by SQLAlchemy)
- Immediate effect without restart
- No race conditions (single process reads latest state)

**Alternatives considered:**
- Redis pub/sub: Over-engineered for single-instance deployment
- File watching: Doesn't apply (config in DB, not files)
- Manual reload endpoint: Requires extra user action

**Implementation:**
```python
class LLMFactory:
    def create_llm(self, provider=None, model=None):
        # Always load fresh from DB
        providers = self._load_providers_from_db()
        # Rest of logic...
```

### 3. Database Schema: Extend Setting Table

**Decision:** Reuse existing `Setting` table with new `setting_type` values: `llm_provider`, `database`.

**Rationale:**
- Consistent with existing pattern (redline, tool, masking)
- No schema migration needed (table already exists)
- Unified settings API

**Alternatives considered:**
- Separate tables (LLMProvider, DatabaseConfig): More normalized but adds complexity
- Key-value store: Less type-safe, harder to query

**Config JSON structure:**
```json
// llm_provider
{
  "provider": "openai|anthropic|azure|custom",
  "api_key": "encrypted_base64",
  "base_url": "https://...",
  "models": ["model1", "model2"],
  "is_primary": true,
  "is_fallback": false
}

// database
{
  "type": "postgresql|redis",
  "host": "localhost",
  "port": 5432,
  "database": "aiops",
  "user": "aiops",
  "password": "encrypted_base64"
}
```

### 4. Frontend State: Zustand Store

**Decision:** Create `settingsStore` following the existing `diagnosisStore` pattern.

**Rationale:**
- Consistency with Investigation page architecture
- Centralized state management
- Easy to add optimistic updates
- Reusable across components

**Alternatives considered:**
- Local component state: Doesn't scale, no reusability
- React Context: More boilerplate than Zustand

**Store structure:**
```typescript
interface SettingsStore {
  llmProviders: LLMProvider[]
  databases: DatabaseConfig[]
  tools: Tool[]
  loading: boolean
  error: string | null

  loadLLMProviders: () => Promise<void>
  addLLMProvider: (data) => Promise<void>
  updateLLMProvider: (id, data) => Promise<void>
  deleteLLMProvider: (id) => Promise<void>
  testLLMProvider: (id) => Promise<TestResult>
  fetchModels: (id) => Promise<string[]>
  // Similar for databases...
}
```

### 5. Permission Control: Decorator-Based Middleware

**Decision:** Use FastAPI dependency injection with `admin_required` decorator.

**Rationale:**
- Declarative and clean
- Reusable across endpoints
- Integrates with existing auth system

**Implementation:**
```python
from app.core.security import get_current_user

def admin_required(user = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Admin access required")
    return user

@router.post("/llm-providers")
def create_provider(data: dict, user = Depends(admin_required)):
    # Only admins can reach here
```

## Risks / Trade-offs

**[Risk] Encryption key loss → All encrypted data unrecoverable**
- Mitigation: Document key backup procedure, warn on first startup
- Trade-off: Security vs. recoverability (chose security)

**[Risk] Hot-reload DB queries add latency to LLM creation**
- Mitigation: SQLAlchemy query caching, acceptable for infrequent operation
- Trade-off: Simplicity vs. performance (chose simplicity)

**[Risk] Breaking change forces manual reconfiguration**
- Mitigation: Auto-migration script on first startup reads env vars and populates DB
- Trade-off: One-time migration effort vs. long-term flexibility

**[Risk] Admin-only access blocks non-admin users from viewing settings**
- Mitigation: Acceptable - settings are system-level, not user-level
- Trade-off: Security vs. transparency (chose security)

**[Risk] Model discovery API calls may fail (rate limits, network issues)**
- Mitigation: Fallback to manual model entry, cache discovered models
- Trade-off: Convenience vs. reliability (support both)

## Migration Plan

**Phase 1: Backend Foundation**
1. Add `encryption.py` with Fernet utilities
2. Add `admin_required` permission decorator
3. Extend Setting model (already supports new types)
4. Add LLM provider CRUD endpoints
5. Add database config endpoints
6. Modify `llm_factory.py` to load from DB

**Phase 2: Auto-Migration**
1. Create `migrate_env_to_db()` function
2. Run on first startup (check if DB has providers)
3. Read env vars (OPENAI_API_KEY, etc.)
4. Create corresponding DB records
5. Log migration results

**Phase 3: Frontend**
1. Create `settingsStore.ts`
2. Create LLM provider components
3. Create database config components
4. Refactor Settings.tsx (remove redline/masking)
5. Update types

**Phase 4: Cleanup**
1. Remove redline/masking components
2. Update documentation
3. Remove env var references from config.py (keep as fallback)

**Rollback Strategy:**
- If migration fails, service falls back to env vars
- Keep env vars in .env.example for emergency fallback
- Database changes are additive (no destructive migrations)

## Open Questions

1. Should we support multiple primary providers (load balancing)? → No, single primary + single fallback sufficient
2. Should encryption key rotation be supported? → Future enhancement, not MVP
3. Should we log all settings changes for audit? → Future enhancement, not MVP
4. Should non-admin users see settings in read-only mode? → No, admin-only for MVP
