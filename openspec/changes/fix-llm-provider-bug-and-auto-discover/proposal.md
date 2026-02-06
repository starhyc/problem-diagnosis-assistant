# Proposal: Fix LLM Provider Bug and Add OpenAI Compatible Auto-Discovery

## Why

The LLM provider configuration has a Pydantic schema mismatch that causes `AttributeError: 'LLMProviderRequest' object has no attribute 'is_default'` when adding new model providers. The database schema was migrated to use `is_default` (replacing `is_primary`/`is_fallback`), but the Pydantic model in `LLMProviderRequest` was never updated.

Additionally, the model discovery feature requires manual clicking of "Auto Discover" button after saving. Industry-standard OpenAI Compatible interfaces automatically fetch available models when base URL and API key are provided, which is the expected behavior.

## What Changes

- **BUG FIX**: Update `LLMProviderRequest`, `LLMProviderResponse`, and `LLMProviderUpdateRequest` schemas to use `is_default` field instead of `is_primary`/`is_fallback`
- **FEATURE**: Enhance `LLMProviderForm` to automatically fetch model list when:
  - Base URL is populated
  - API Key is provided
  - User focuses on model name input field
- **FEATURE**: Add dropdown selection for discovered models with the ability to manually add custom models
- **FEATURE**: Support "OpenAI Compatible" mode with unified model discovery UX

## Capabilities

### New Capabilities

- `openai-compatible-model-discovery`: Enables automatic model list fetching from OpenAI-compatible endpoints (including custom providers). Features include:
  - Auto-trigger on field changes with debouncing
  - Dropdown selector for available models
  - Manual model entry fallback
  - Support for provider types: OpenAI, Azure OpenAI, and Custom (OpenAI Compatible)

### Modified Capabilities

- `llm-provider-management` (existing spec): UPDATE requirement for model discovery to include auto-trigger behavior
- `multi-llm-provider` (existing spec): NO requirement changes (implementation only)
- `settings-ui` (existing spec): NO requirement changes (implementation only)

## Impact

### Backend Changes

**Files affected:**
- `server/app/schemas/case.py:169-198` - Pydantic schema update
  - `LLMProviderRequest`: Add `is_default` field, remove `is_primary`/`is_fallback`
  - `LLMProviderResponse`: Add `is_default` field, remove `is_primary`/`is_fallback`
  - `LLMProviderUpdateRequest`: Add `is_default` field, remove `is_primary`/`is_fallback`
- `server/app/api/v1/endpoints/settings.py` - No API changes needed (already uses `is_default`)
- Database: Already migrated, no changes needed

### Frontend Changes

**Files affected:**
- `src/components/settings/LLMProviderForm.tsx:1-200` - Add auto-discovery on input, add model dropdown
- `src/store/settingsStore.ts` - No API changes needed
- `src/types/settings.ts` - Already uses `is_default`

### Dependencies

- Pydantic < 2.0 (affected by schema changes)
- Existing database migration 002 already uses `is_default` column

### Breaking Changes

**BREAKING**: Backend Pydantic schema field names changed
- `is_primary` → `is_default`
- `is_fallback` → `is_default` (fallback logic simplified to single default provider)

This affects:
- Frontend form submission (uses `is_default` - already correct)
- Any external API consumers using the old field names

### Non-Breaking Changes

- Backend API endpoints remain compatible (already using `is_default`)
- Database schema already migrated
- Frontend types already use `is_default`
