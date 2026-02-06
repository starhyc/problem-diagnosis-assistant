# Implementation Tasks: LLM Provider Bug Fix and Auto-Discovery

## 1. Backend - Pydantic Schema Fix

- [x] 1.1 Update `LLMProviderRequest` in `server/app/schemas/case.py`
  - Change `is_primary: bool` → `is_default: bool`
  - Remove `is_fallback` field
  - Keep default value as `False`

- [x] 1.2 Update `LLMProviderResponse` in `server/app/schemas/case.py`
  - Change `is_primary: bool` → `is_default: bool`
  - Remove `is_fallback` field

- [x] 1.3 Update `LLMProviderUpdateRequest` in `server/app/schemas/case.py`
  - Change `is_primary Optional[bool]` → `is_default Optional[bool]`
  - Remove `is_fallback` field

- [x] 1.4 Verify endpoint compatibility
  - Check `server/app/api/v1/endpoints/settings.py` already uses `is_default`
  - Verify no endpoint code uses `is_primary` or `is_fallback`
  - Run backend tests if any exist

## 2. Frontend - Debounced Auto-Discovery Logic

- [x] 2.1 Add debounced discovery hook to `LLMProviderForm.tsx`
  - Use `useEffect` + `setTimeout` with 800ms debounce
  - Create `shouldAutoDiscover()` helper for conditional triggering
  - Reset debounce on form change

- [x] 2.2 Implement auto-discovery state management
  - Add `discovering` state for progress indicator
  - Add `discovererror` state for failure handling
  - Track debounced timer for cleanup

- [x] 2.3 Add detection logic for provider-specific behavior
  - OpenAI: Always auto-discover when API key present
  - Custom: Auto-discover when API key AND base URL present
  - Azure: Auto-discover when API key AND base URL present
  - Anthropic: Skip auto-discover (use predefined models)

## 3. Frontend - Model Selection UI

- [x] 3.1 Create model dropdown component
  - Show discovered models in scrollable list
  - Add filter/search input at top
  - Click handler to add selected model

- [x] 3.2 Update manual model entry section
  - Keep "手动添加模型" (Manual add) input visible always
  - Update placeholder text based on discovery status

- [x] 3.3 Implement model list display
  - Show current models as removable tags (existing behavior)
  - Ensure discovered and manually added models both show
  - Visual distinction for discovered vs manual (optional)

## 4. Frontend - Error Handling & Recovery

- [x] 4.1 Add error state UI for discovery failures
  - Error toast for API failures
  - HTTPS-insecure-note for local API
  - Timeout message (10s) with retry button

- [x] 4.2 Add retry discovery button
  - Display when auto-discovery fails
  - Bypasses debounce, triggers immediate discovery

- [x] 4.3 Maintain form usability on errors
  - Ensure manual entry always works
  - Don't block user from attempting save

## 5. Frontend - Progressive Enhancement

- [x] 5.1 Ensure "Auto Discover" button still works
  - Keep existing manual `handleDiscoverModels` function
  - Existing button should function independently

- [x] 5.2 Respect existing provider editing workflow
  - Load provider data on edit check
  - Preserve existing "Add/Remove Model" behavior

## 6. Testing & Verification

- [ ] 6.1 Verify Pydantic schema change
  - Create provider with `is_default: true`
  - Verify it's stored correctly in database
  - Verify GET endpoint returns `is_default`

- [ ] 6.2 Verify auto-discovery (OpenAI)
  - Enter valid OpenAI API key → model list loads
  - Enter invalid API key → error shown, manual entry works
  - Debounce works (no API call during typing)

- [ ] 6.3 Verify auto-discovery (Custom)
  - Enter API key + valid base URL → model list loads
  - Enter API key only → no auto-discovery trigger
  - Custom models must support `/models` endpoint

- [ ] 6.4 Verify model selection
  - Discovered models can be added
  - Manual models can be added
  - Duplicate prevention works (or handled gracefully)
  - Model removal works for both types

- [ ] 6.5 Verify form submission
  - Save with discovered models
  - Save with manually added models
  - Save with mixed discovered + manual

## 7. Cleanup & Code Review

- [ ] 7.1 Remove dead code
  - Check for references to `is_primary` or `is_fallback` in codebase
  - Check for unused discovery-related state

- [ ] 7.2 Add console warnings for edge cases
  - Fetch failures (don't need user-facing toast, already handled)
  - CORS issues for custom endpoints (show in toast)

- [ ] 7.3 Verify linting and type checking
  - Run `pnpm lint` on frontend
  - Verify no TypeScript errors
  - Check backend hasn't broken imports
