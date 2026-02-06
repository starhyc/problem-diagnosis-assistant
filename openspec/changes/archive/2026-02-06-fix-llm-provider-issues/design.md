## Context

The LLM provider management system has three issues:
1. **Backend TypeError**: `setting_repo.create()` is called with a dict as positional arg, but the `@with_session` decorator expects keyword args
2. **Missing auto-discovery UX**: Users must manually type model names; no auto-fetch on input focus
3. **Form styling confusion**: Empty input fields appear to have default values due to unclear visual state

Current state:
- Backend uses `BaseRepository.create(self, session, **kwargs)` with `@with_session` decorator
- Frontend has auto-discovery logic but only triggers on field changes for saved providers
- Form inputs use `bg-bg-surface` (white) for all states

## Goals / Non-Goals

**Goals:**
- Fix TypeError to allow saving new LLM providers
- Enable model auto-discovery when user focuses the manual input field
- Improve visual clarity of empty vs filled form fields

**Non-Goals:**
- Redesigning the entire LLM provider management UI
- Adding new provider types or capabilities
- Changing the database schema

## Decisions

### Decision 1: Fix create() calls with dict unpacking
**Approach**: Add `**` operator to unpack dict arguments in all `setting_repo.create()` calls

**Rationale**: The `@with_session` decorator injects `session` as the second parameter, so calling `create({...})` results in `f(self, session, dict_obj)` which fails. Using `create(**{...})` properly unpacks to keyword args.

**Alternatives considered**:
- Modify `@with_session` decorator: Would affect all repository methods, higher risk
- Change `BaseRepository.create()` signature: Would break other code using this pattern

**Locations to fix**:
- `server/app/api/v1/endpoints/settings.py:111`
- `server/app/core/migration.py:35, 55, 75`

### Decision 2: Trigger auto-discovery on input focus
**Approach**: Add `onFocus` handler to manual model input field that calls existing auto-discovery logic

**Rationale**: Reuses existing `autoDiscoverModels()` function and backend endpoint. Only triggers if credentials are present (api_key + base_url for applicable providers).

**Alternatives considered**:
- Create new backend endpoint for temporary discovery: Unnecessary complexity
- Client-side API calls: CORS issues, security concerns with exposing API keys

**Implementation**: Add `onFocus` handler at `LLMProviderForm.tsx:312-320` that checks credentials and calls `autoDiscoverModels()`

### Decision 3: Improve form field visual state
**Approach**: Add placeholder text and subtle border color change for empty fields

**Rationale**: Minimal change that provides visual feedback without redesigning the form. Users currently see empty strings as "default values" because there's no visual distinction.

**Implementation**:
- Add meaningful placeholder text to name and api_key inputs
- Consider adding `focus:` state styling for better UX

## Risks / Trade-offs

**Risk**: Auto-discovery on focus may trigger too frequently if user tabs through fields
→ **Mitigation**: Only trigger if credentials are valid and models not already fetched

**Risk**: Form styling changes may conflict with design system
→ **Mitigation**: Use existing Tailwind classes and maintain consistency with other forms

**Trade-off**: Auto-discovery for new providers requires valid credentials before fetching
→ **Accepted**: This is expected behavior; can't fetch models without authentication

## Migration Plan

No migration needed - these are bug fixes and UX improvements. Changes are backwards compatible.

**Deployment**:
1. Deploy backend fixes first (critical bug fix)
2. Deploy frontend changes (UX improvements)

**Rollback**: Standard git revert if issues arise
