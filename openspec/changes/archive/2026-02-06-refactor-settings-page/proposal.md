## Why

The current Settings page has hardcoded LLM and database configurations in environment variables, making it impossible to dynamically add/switch providers or update configurations without restarting the service. This creates operational friction and prevents runtime flexibility for managing critical system dependencies.

## What Changes

- Remove redline rules and masking rules features (not core requirements)
- Add LLM provider management with CRUD operations, connection testing, and model discovery
- Add database configuration management with connection testing
- Implement encrypted storage for API keys and passwords
- Add admin-only permission controls for all settings operations
- Enable hot-reload for configuration changes (immediate effect without restart)
- Completely deprecate environment variable configuration in favor of database-backed settings
- Refactor Settings page UI to focus on LLM providers, databases, and external tools only

**BREAKING**: Environment variables for LLM providers (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.) and database configuration will no longer be used. All configuration must be done through the Settings UI.

## Capabilities

### New Capabilities
- `llm-provider-management`: Manage LLM providers (OpenAI, Anthropic, Azure OpenAI, custom) with CRUD operations, connection testing, model discovery, and primary/fallback selection
- `database-configuration`: Manage PostgreSQL and Redis connection settings with encrypted credential storage and connection testing
- `settings-encryption`: Encrypt/decrypt sensitive configuration data (API keys, passwords) at rest
- `settings-hot-reload`: Apply configuration changes immediately without service restart

### Modified Capabilities
- `external-tools`: Existing tool management remains but redline/masking features removed

## Impact

**Backend:**
- `server/app/core/llm_factory.py` - Load providers from database instead of env vars
- `server/app/core/config.py` - Deprecate LLM/DB env variables
- `server/app/api/v1/endpoints/settings.py` - Add LLM provider and database CRUD endpoints
- `server/app/repositories/setting_repository.py` - Add encryption/decryption methods
- `server/app/models/case.py` - Setting model supports new types (llm_provider, database)
- New: `server/app/core/encryption.py` - Cryptography utilities for sensitive data
- New: `server/app/middleware/permissions.py` - Admin permission checks

**Frontend:**
- `src/pages/Settings.tsx` - Refactor to 2 tabs (LLM Providers, Databases, External Tools)
- `src/store/settingsStore.ts` - New Zustand store for settings state management
- `src/components/settings/LLMProviderList.tsx` - New component
- `src/components/settings/LLMProviderForm.tsx` - New component
- `src/components/settings/DatabaseConfig.tsx` - New component
- Remove: `src/components/settings/RedlineList.tsx`
- Remove: `src/components/settings/MaskingRules.tsx`
- `src/types/settings.ts` - Update types for new capabilities

**Database:**
- Setting table extended with new setting_type values: 'llm_provider', 'database'
- Migration script to move env var configs to database on first startup

**Security:**
- All settings endpoints require admin role
- API keys and passwords encrypted using Fernet (symmetric encryption)
- Encryption key stored securely (separate from database)
