## Why

The LLM provider management system has three issues preventing proper functionality: (1) a critical backend TypeError that blocks saving new providers, (2) missing auto-discovery UX when users click the model input field, and (3) confusing form styling where empty fields appear to have default values.

## What Changes

- **Fix backend TypeError**: Unpack dict arguments in `setting_repo.create()` calls (4 locations: settings.py and migration.py)
- **Add click-to-fetch model discovery**: Trigger model auto-discovery when user clicks/focuses the manual model input field for new providers
- **Improve form field UX**: Add visual distinction between empty and filled input states to prevent confusion about default values

## Capabilities

### New Capabilities
<!-- None - these are fixes to existing functionality -->

### Modified Capabilities
<!-- No spec-level requirement changes - implementation fixes only -->

## Impact

**Backend**:
- `server/app/api/v1/endpoints/settings.py:111` - Fix create() call in create_llm_provider
- `server/app/core/migration.py:35,55,75` - Fix create() calls in migration functions

**Frontend**:
- `src/components/settings/LLMProviderForm.tsx` - Add onFocus handler for model input, improve input styling

**Breaking Changes**: None

**Database**: No schema changes required
