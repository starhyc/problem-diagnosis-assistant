## Why

The current settings architecture stores all configuration (LLM providers, external tools, database configs) in a single `settings` table with a generic JSON `config` column. This creates schema ambiguity, prevents database-level validation, and makes queries inefficient. Additionally, several critical bugs exist: HTTP method mismatches break model discovery, encryption keys auto-generate silently causing data loss, and tool connection testing is stubbed out.

## What Changes

- **Split settings table into dedicated tables**: `llm_providers`, `external_tools`, `database_configs` with proper typed columns
- **Fix HTTP method mismatch**: Frontend `fetchModels()` sends POST but backend expects GET
- **Improve encryption key management**: Fail fast in production if `ENCRYPTION_KEY` not set, loud warning in development
- **Add auto-promotion for default provider**: When deleting the default LLM provider, automatically promote the next enabled provider
- **Implement real tool connection testing**: Replace stub with actual HTTP connection tests, store test results
- **Add config validation**: Use Pydantic models to validate provider-specific configurations (Azure requires `deployment`, etc.)
- **Remove unused database settings API**: Clean up endpoints that conflict with environment-only configuration policy

## Capabilities

### New Capabilities
- `llm-provider-config-validation`: Validate LLM provider configurations using Pydantic models specific to each provider type (OpenAI, Anthropic, Azure, Custom)

### Modified Capabilities
- `llm-provider-management`: Add auto-promotion behavior when deleting default provider, fix HTTP method for model discovery
- `external-tools`: Implement real connection testing with status tracking
- `settings-encryption`: Change behavior to fail fast in production when encryption key is missing
- `database-configuration`: Remove UI and API endpoints (configuration remains environment-only per CLAUDE.md)

## Impact

**Backend**:
- `server/app/models/case.py`: Replace `Setting` model with `LLMProvider`, `ExternalTool`, `DatabaseConfig` models
- `server/app/repositories/setting_repository.py`: Split into dedicated repositories or update to handle new models
- `server/app/api/v1/endpoints/settings.py`: Update all endpoints to use new models, add validation, fix HTTP methods
- `server/app/core/encryption.py`: Update initialization logic to fail fast in production
- `server/app/schemas/case.py`: Add Pydantic validation models for each provider type
- Database migration required to split tables and migrate existing data

**Frontend**:
- `src/lib/api.ts`: Fix `fetchModels()` HTTP method, remove database settings endpoints
- `src/store/settingsStore.ts`: No changes needed (API contract remains compatible)
- `src/components/settings/`: No changes needed (UI remains the same)

**Breaking Changes**:
- **BREAKING**: Database schema change requires migration
- **BREAKING**: Encryption key now required in production (will fail to start without it)
