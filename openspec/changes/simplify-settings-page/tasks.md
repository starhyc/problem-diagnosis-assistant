## 1. Database Migration

- [x] 1.1 Create migration script to add `is_default` column to settings table
- [x] 1.2 Add data migration logic to set `is_default = is_primary` for existing records
- [x] 1.3 Add unique constraint on `is_default = true` per setting type
- [x] 1.4 Drop `is_primary` and `is_fallback` columns after migration
- [ ] 1.5 Test migration with sample data

## 2. Backend - Type Definitions

- [x] 2.1 Update LLMProvider schema in `server/app/repositories/setting_repository.py` to use `is_default`
- [x] 2.2 Remove `is_primary` and `is_fallback` from provider schema

## 3. Backend - LLM Factory

- [x] 3.1 Update `server/app/core/llm_factory.py` to read `is_default` instead of `is_primary`
- [x] 3.2 Update fallback logic to use enabled non-default providers as fallback chain
- [x] 3.3 Update `_load_providers_from_db()` to handle `is_default` flag

## 4. Backend - API Endpoints

- [x] 4.1 Remove database configuration endpoints from `server/app/api/v1/endpoints/settings.py`
- [x] 4.2 Update LLM provider endpoints to handle `is_default` field
- [x] 4.3 Add validation to ensure only one provider can be default

## 5. Frontend - Type Definitions

- [x] 5.1 Update `LLMProvider` interface in `src/types/settings.ts` to replace `is_primary`/`is_fallback` with `is_default`
- [x] 5.2 Remove `DatabaseConfig` interface from `src/types/settings.ts`
- [x] 5.3 Remove `SettingsData.databases` field

## 6. Frontend - Store

- [x] 6.1 Remove database-related methods from `src/store/settingsStore.ts` (loadDatabases, updateDatabase, testDatabase)
- [x] 6.2 Remove `databases` state from settingsStore
- [x] 6.3 Update LLM provider methods to handle `is_default` field

## 7. Frontend - LLM Provider Form

- [x] 7.1 Fix label styling in `src/components/settings/LLMProviderForm.tsx` by adding `text-text-main` class to all labels (lines 83, 94, 108, 119, 130)
- [x] 7.2 Replace `is_primary` and `is_fallback` checkboxes with single `is_default` radio button
- [x] 7.3 Update form state to use `is_default` field
- [x] 7.4 Update form submission to send `is_default` instead of `is_primary`/`is_fallback`

## 8. Frontend - LLM Provider List

- [x] 8.1 Update `src/components/settings/LLMProviderList.tsx` to display "默认" badge instead of "主要"/"备用"
- [x] 8.2 Update badge logic to check `is_default` instead of `is_primary`/`is_fallback`

## 9. Frontend - Settings Page Layout

- [x] 9.1 Remove tab navigation from `src/pages/Settings.tsx`
- [x] 9.2 Implement collapsible section component with expand/collapse state
- [x] 9.3 Add localStorage persistence for section expanded/collapsed state
- [x] 9.4 Set default state to all sections expanded on first visit
- [x] 9.5 Replace tab content rendering with collapsible sections for LLM and Tools
- [x] 9.6 Remove database section entirely

## 10. Frontend - Cleanup

- [x] 10.1 Delete `src/components/settings/DatabaseConfig.tsx` file
- [x] 10.2 Remove DatabaseConfig import from Settings.tsx
- [x] 10.3 Remove database tab button and related state

## 11. Configuration Documentation

- [x] 11.1 Update `server/.env.example` to document all database connection variables
- [x] 11.2 Update `server/CLAUDE.md` to reflect .env-only database configuration approach
- [x] 11.3 Add migration notes to documentation

## 12. Testing

- [ ] 12.1 Test LLM provider creation with `is_default` flag
- [ ] 12.2 Test that only one provider can be default at a time
- [ ] 12.3 Test default provider deletion validation
- [ ] 12.4 Test collapsible sections expand/collapse functionality
- [ ] 12.5 Test localStorage persistence of section state
- [ ] 12.6 Verify form labels are visible in modal
- [ ] 12.7 Test migration script with existing data
