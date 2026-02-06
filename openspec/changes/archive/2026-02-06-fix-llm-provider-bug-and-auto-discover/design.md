# Design: LLM Provider Bug Fix and Auto-Model Discovery

## Context

### Current State

**Backend Bug:**
- Database migration 002 added `is_default` column to settings table
- Pydantic schemas in `server/app/schemas/case.py` still use `is_primary` and `is_fallback`
- Endpoint at `server/app/api/v1/endpoints/settings.py:99` tries to access `data.is_default` causing AttributeError

**Frontend Limitation:**
- `LLMProviderForm.tsx` has "Auto Discover" button but requires:
  1. User saves provider first (may fail due to bug)
  2. User re-opens edit modal
  3. User clicks "Auto Discover" button
  4. Models load

This is not aligned with industry-standard OpenAI Compatible experience where models are discovered immediately when API key and endpoint are provided.

### Stakeholders

- **Backend**: Admin users configuring LLM providers
- **Frontend**: Admin users managing system configuration

## Goals / Non-Goals

**Goals:**
- Fix Pydantic schema mismatch to unblock model provider creation
- Enable immediate model discovery when both base URL and API key are entered
- Provide seamless "OpenAI Compatible" experience for custom endpoints
- Maintain backward compatibility with existing providers

**Non-Goals:**
- Change backend API contract (existing endpoints remain same)
- Modify database schema (already migrated)
- Redesign settings page layout
- Support real-time model list updates (on-demand fetch is sufficient)

## Decisions

### 1. Fix Pydantic Schema to Match Database Migration

**Decision:** Update `LLMProviderRequest`, `LLMProviderResponse`, and `LLMProviderUpdateRequest` to use `is_default` field.

**Rationale:**
- Database already has `is_default` column (migration 002)
- Frontend types already use `is_default`
- Endpoint already tries to access `is_default`
- Only the Pydantic schema is out of sync

**Implementation:**
```python
# server/app/schemas/case.py
class LLMProviderRequest(BaseModel):
    name: str
    provider: str
    api_key: str
    base_url: Optional[str] = None
    models: Optional[List[str]] = None
    is_default: bool = False  # ✅ Changed from is_primary
    # is_fallback removed - single default provider model
```

**Alternative Considered:** Add migration to revert database to match Pydantic (reject - database is source of truth, frontend already uses `is_default`)

### 2. Auto-Fetch Models on Field Changes (Debounced)

**Decision:** Use debounced effect to trigger model discovery when both API key and base URL (if required) are populated.

**Debouncing Strategy:**
- Debounce time: 800ms (1.3 seconds user idle)
- Trigger when: `api_key.length > 0` AND (provider === 'openai', 'custom' OR base_url.length > 0 for azure/custom)

**UI Pattern:**
```
┌─────────────────────────────────────────┐
│ API Key: sk-...                         │
│ Base URL: https://api.endpoint.com/v1   │
│                                         │
│ [🔍 Discovering models...]              │
│ ━━━━━━━━━━━━━━━━━━━━━━░░░░ 75%         │
└─────────────────────────────────────────┘
```

**Alternative Considered:**
- Fetch immediately on input change (reject - too many API calls)
- Fetch only on blur (reject - poor UX, requires manual action)
- Fetch only when clicking "Search" button (reject - same as current)

### 3. Model Selection UI - Dropdown with Manual Entry

**Decision:** Horizontal layout with model list to the side, manual input with "Add" button below.

```
┌─────────────────────────────────────────────────────┐
│ 模型列表 / Model List                                │
├─────────────────────────────────────────────────────┤
│ Available Models: (when discovered)                  │
│ ┌────────────────────────────────────────────────┐  │
│ │ ▼ GPT-4o                                     │  │  │
│ │   gpt-4o-mini                               │  │  │
│ │   o1-preview                                │  │  │
│ │   [Click to select model]                    │  │  │
│ └────────────────────────────────────────────────┘  │
│                                                     │
│ Add Model Manually:                                 │
│ ┌──────────────┐ ┌──────┐                          │
│ │ model-name │  │ Add  │                          │
│ └──────────────┘ └──────┘                          │
│                                                     │
│ Current Models:                                     │
│ • gpt-4o-mini  [×]                                 │
│ • custom-model [×]                                  │
└─────────────────────────────────────────────────────┘
```

**Implementation Approach:**
1. When models are discovered successfully, populate a "Available Models" dropdown
2. Clicking an available model adds it to `formData.models`
3. Manual input allows adding custom model names not in discovery results

**Alternative Considered:**
- Full dropdown without manual entry (reject - blocks custom finetuned models)
- Autocomplete with free text (reject - requires more complex component)

### 4. Provider Type Detection for Auto-Discovery

**Decision:** Model discovery behavior varies by provider type:

| Provider | Auto-Discovery Behavior |
|----------|-------------------------|
| OpenAI | ✓ Auto-fetch from `/v1/models` endpoint |
| Anthropic | ✓ Return hardcoded known models |
| Azure | ✓ Requires deployment name (auto-discover uses deployment list) |
| Custom | ✓ Use OpenAI-compatible mode (`/models` endpoint) |

**Detection Logic:**
```typescript
const shouldAutoDiscover =
  apiKey &&
  (provider === 'openai' ||
   (provider === 'custom' && baseUrl) ||
   (provider === 'azure' && baseUrl))
```

### 5. Error Handling for Discovery Failures

**Decision:** Graceful fallback to manual entry mode.

**Patterns:**
1. API call fails → Show error toast, keep forms visible
2. Malformed response → Show error toast, enable manual input
3. No models returned → Show "No models found" message, enable manual input
4. Network timeout (10s) → Timeout error with retry button

**UI:**
```
┌─────────────────────────────────────────┐
│ ❌ Model discovery failed                │
│ Error: Connection timeout (10s)          │
│ [⟳ Retry discovery]                      │
│                                          │
│ You can still add models manually:       │
│ ┌──────────────┐ ┌──────┐                │
│ │ model-name │  │ Add  │                │
│ └──────────────┘ └──────┘                │
└─────────────────────────────────────────┘
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **Breaking changes in Pydantic schemas** affects external integrations | Document in changelog, maintain API compatibility for existing endpoints (already using `is_default`) |
| **Too many discovery API calls** on rapid typing | Debounce with 800ms delay |
| **Provider returns unexpected model format** | Validate response shape, fallback to error + manual entry |
| **Custom providers don't support `/models` endpoint** | Error, provide manual entry path |
| **Discovery takes too long (network latency)** | 10s timeout + progress indicator |
| **User expects real-time updates** | Document that discovery is on-demand |
| **FF Accuracy:** Only fetch when API key validates | Can't pre-validate API key without making actual call |
| **CORS issues** with custom endpoints | Show browser console error in toast, suggest manual entry |

## Migration Plan

### Backend (Zero-Downtime)

1. **Deploy backend changes:**
   ```bash
   # server/app/schemas/case.py
   # Change is_primary/is_fallback → is_default
   ```

2. **Verification:**
   - Existing providers with `is_default` in database continue working
   - New providers with `is_default` field work correctly
   - No data loss (database already migrated)

### Frontend (Progressive Enhancement)

1. **Deploy frontend changes:**
   - `src/components/settings/LLMProviderForm.tsx` auto-discovery UI
   - No config changes required

2. **User Migration:**
   - Existing users see new auto-discovery feature immediately
   - Manual "Auto Discover" button still available for older workflows
   - No user action required

### Rollback Plan

**Backend rollback:**
- Revert `LLMProviderRequest` schema to `is_primary`/`is_fallback`
- Endpoint code will break (expects `is_default`)
- Requires database revert migration

**Frontend rollback:**
- Revert `LLMProviderForm.tsx` changes
- Users lose auto-discovery feature
- Manual workflow still works

## Open Questions

1. **Discovery frequency limit:** Should we rate-limit discovery calls per API key? (Current: No limit)
2. **Model list persistence:** Cache discovered models in localStorage? (Current: No cache, always fetch)
3. **UI language:** Should dropdown labels be bilingual (中文/English)? (Current: All Chinese)
4. **Azure deployment discovery:** Azure requires deployment names - should discovery list deployments or just validate? (Current: Mentioned as complex, leaving for future)
