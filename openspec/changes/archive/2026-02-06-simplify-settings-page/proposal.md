## Why

The current settings page uses a tab-based layout that fragments related configuration options and creates unnecessary navigation overhead. The LLM provider configuration uses a complex primary/fallback model that's harder to understand than a simple default model approach. Additionally, database configuration exposed in the UI creates security risks and violates 12-factor app principles - infrastructure config belongs in environment variables.

## What Changes

- **Remove database configuration UI** - Move PostgreSQL and Redis config to .env only
- **Simplify LLM model selection** - Replace `is_primary`/`is_fallback` flags with single `is_default` flag
- **Redesign settings layout** - Replace tab navigation with single-page collapsible sections
- **Fix styling bug** - Add missing text color classes to form labels in LLMProviderForm
- **Consolidate settings display** - Show LLM providers and external tools in unified view with collapsible sections

## Capabilities

### New Capabilities
- `settings-single-page-layout`: Single-page settings interface with collapsible sections for better UX and reduced navigation overhead

### Modified Capabilities
- `llm-provider-management`: Simplify model selection from primary/fallback to default model concept
- `settings-ui`: Remove database configuration UI, keep only LLM and external tools

## Impact

**Frontend:**
- `src/pages/Settings.tsx` - Remove tab navigation, implement collapsible sections
- `src/components/settings/LLMProviderForm.tsx` - Fix label styling, update form fields
- `src/components/settings/LLMProviderList.tsx` - Update to show default badge instead of primary/fallback
- `src/components/settings/DatabaseConfig.tsx` - **DELETE** (move to .env)
- `src/store/settingsStore.ts` - Remove database-related methods
- `src/types/settings.ts` - Update LLMProvider interface, remove DatabaseConfig

**Backend:**
- `server/app/core/llm_factory.py` - Update to use `is_default` instead of `is_primary`/`is_fallback`
- `server/app/api/v1/endpoints/settings.py` - Remove database config endpoints
- `server/app/repositories/setting_repository.py` - Update LLM provider schema
- Database migration needed for `settings` table schema change

**Configuration:**
- `server/.env.example` - Document all database connection variables
- `server/CLAUDE.md` - Update documentation to reflect .env-only database config
