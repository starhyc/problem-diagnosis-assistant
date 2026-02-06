## 1. Backend: Fix TypeError in Repository Calls

- [x] 1.1 Fix `setting_repo.create()` call in `server/app/api/v1/endpoints/settings.py:111` by unpacking dict with `**`
- [x] 1.2 Fix `setting_repo.create()` call in `server/app/core/migration.py:35` (OpenAI migration)
- [x] 1.3 Fix `setting_repo.create()` call in `server/app/core/migration.py:55` (Anthropic migration)
- [x] 1.4 Fix `setting_repo.create()` call in `server/app/core/migration.py:75` (Azure migration)

## 2. Frontend: Add Auto-Discovery on Input Focus

- [x] 2.1 Add `onFocus` handler to manual model input field in `src/components/settings/LLMProviderForm.tsx:312-320`
- [x] 2.2 Implement credential validation check before triggering auto-discovery
- [x] 2.3 Call existing `autoDiscoverModels()` function when focus occurs and credentials are valid

## 3. Frontend: Improve Form Field Visual State

- [x] 3.1 Add meaningful placeholder text to name input field
- [x] 3.2 Add meaningful placeholder text to api_key input field
- [x] 3.3 Add focus state styling to improve visual feedback

## 4. Testing

- [x] 4.1 Test creating new LLM provider (verify TypeError is fixed)
- [x] 4.2 Test auto-discovery triggers on input focus for new providers
- [x] 4.3 Test form field visual states (empty, focused, filled)
- [x] 4.4 Test migration script with fixed create() calls
