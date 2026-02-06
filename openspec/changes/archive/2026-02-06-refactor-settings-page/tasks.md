## 1. Backend - Encryption Infrastructure

- [x] 1.1 Create `server/app/core/encryption.py` with Fernet encryption/decryption utilities
- [x] 1.2 Add encryption key generation and validation on startup
- [x] 1.3 Add `ENCRYPTION_KEY` to config.py with auto-generation fallback
- [x] 1.4 Add encryption/decryption methods to SettingRepository

## 2. Backend - Permission Control

- [x] 2.1 Create `server/app/middleware/permissions.py` with `admin_required` dependency
- [x] 2.2 Integrate admin_required with existing auth system

## 3. Backend - LLM Provider Management

- [x] 3.1 Add LLM provider CRUD endpoints to `server/app/api/v1/endpoints/settings.py`
- [x] 3.2 Add test connection endpoint for LLM providers
- [x] 3.3 Add model discovery endpoint (fetch from provider API)
- [x] 3.4 Add manual model addition endpoint
- [x] 3.5 Add primary/fallback selection validation logic
- [x] 3.6 Create Pydantic schemas for LLM provider requests/responses

## 4. Backend - Database Configuration

- [x] 4.1 Add database configuration CRUD endpoints to settings.py
- [x] 4.2 Add PostgreSQL connection test endpoint
- [x] 4.3 Add Redis connection test endpoint
- [x] 4.4 Create Pydantic schemas for database config requests/responses

## 5. Backend - LLM Factory Hot-Reload

- [x] 5.1 Modify `server/app/core/llm_factory.py` to load providers from database
- [x] 5.2 Add fallback to environment variables if database is empty
- [x] 5.3 Remove hardcoded provider initialization
- [x] 5.4 Add configuration caching per request
- [x] 5.5 Add error handling for configuration reload failures

## 6. Backend - Environment Variable Migration

- [x] 6.1 Create migration function to move env vars to database on first startup
- [x] 6.2 Add migration check in main.py startup event
- [x] 6.3 Log migration results and warnings

## 7. Backend - Remove Unused Features

- [x] 7.1 Remove redline endpoints from settings.py
- [x] 7.2 Remove masking endpoints from settings.py
- [x] 7.3 Keep Setting model generic (supports all types)

## 8. Frontend - Type Definitions

- [x] 8.1 Update `src/types/settings.ts` with LLMProvider interface
- [x] 8.2 Add DatabaseConfig interface
- [x] 8.3 Add TestResult interface
- [x] 8.4 Remove Redline and MaskingRule interfaces

## 9. Frontend - Settings Store

- [ ] 9.1 Create `src/store/settingsStore.ts` with Zustand
- [ ] 9.2 Add LLM provider state and actions (load, add, update, delete, test, fetchModels)
- [ ] 9.3 Add database config state and actions (load, update, test)
- [ ] 9.4 Add tools state and actions (keep existing functionality)
- [ ] 9.5 Add loading and error state management

## 10. Frontend - API Client

- [ ] 10.1 Add LLM provider API methods to `src/lib/api.ts`
- [ ] 10.2 Add database config API methods
- [ ] 10.3 Remove redline and masking API methods

## 11. Frontend - LLM Provider Components

- [ ] 11.1 Create `src/components/settings/LLMProviderList.tsx`
- [ ] 11.2 Create `src/components/settings/LLMProviderForm.tsx` with modal
- [ ] 11.3 Add connection test UI with status indicators
- [ ] 11.4 Add model discovery UI with manual entry fallback
- [ ] 11.5 Add primary/fallback selection UI

## 12. Frontend - Database Configuration Component

- [ ] 12.1 Create `src/components/settings/DatabaseConfig.tsx`
- [ ] 12.2 Add PostgreSQL configuration form
- [ ] 12.3 Add Redis configuration form
- [ ] 12.4 Add connection test UI for both databases

## 13. Frontend - Settings Page Refactor

- [ ] 13.1 Refactor `src/pages/Settings.tsx` to use settingsStore
- [ ] 13.2 Update tabs to show LLM Providers, Databases, External Tools
- [ ] 13.3 Remove redline and masking tabs
- [ ] 13.4 Add admin permission check on page load

## 14. Frontend - Cleanup

- [ ] 14.1 Delete `src/components/settings/RedlineList.tsx`
- [ ] 14.2 Delete `src/components/settings/MaskingRules.tsx`
- [ ] 14.3 Update settings component index exports

## 15. Testing and Validation

- [ ] 15.1 Test LLM provider CRUD operations
- [ ] 15.2 Test encryption/decryption of API keys
- [ ] 15.3 Test connection testing for all provider types
- [ ] 15.4 Test model discovery and manual entry
- [ ] 15.5 Test primary/fallback provider switching
- [ ] 15.6 Test database configuration and connection testing
- [ ] 15.7 Test hot-reload (config changes take effect immediately)
- [ ] 15.8 Test admin permission enforcement
- [ ] 15.9 Test environment variable migration on first startup
- [ ] 15.10 Verify redline/masking features are completely removed
