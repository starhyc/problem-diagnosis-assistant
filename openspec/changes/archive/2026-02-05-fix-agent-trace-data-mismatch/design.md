## Context

The diagnosis workbench uses WebSocket to stream agent execution traces from backend to frontend. The backend demo (`demo_trace.py`) sends messages with field names that don't match the frontend TypeScript interfaces, causing display issues. Additionally, the CenterPanel currently displays legacy `currentCase.messages` data instead of the real-time trace data.

**Current Issues:**
- Backend sends `stepType`/`stepId`, frontend expects `type`/`id`
- Backend doesn't send `taskDescription` or `subtasks` in `agent_trace_start`
- CenterPanel uses outdated data source (`currentCase.messages`)

## Goals / Non-Goals

**Goals:**
- Fix field name mismatches between backend and frontend
- Add missing fields to backend WebSocket messages
- Create global timeline view showing all agent steps chronologically
- Replace CenterPanel data source with real-time trace data

**Non-Goals:**
- Changing the overall trace data structure or WebSocket message types
- Modifying AgentTracePanel behavior (it works correctly)
- Refactoring unrelated components

## Decisions

### Decision 1: Map fields in frontend store vs fix backend

**Chosen:** Map fields in `diagnosisStore.ts` when receiving WebSocket messages

**Rationale:**
- Frontend is more flexible to change than backend protocol
- Allows backend to maintain consistent naming if other clients exist
- Centralized mapping in one location (store)
- No breaking changes to WebSocket protocol

**Alternative considered:** Change backend field names
- Would require coordinating backend/frontend deployment
- May break other consumers of the WebSocket API

### Decision 2: Backend adds missing fields vs frontend handles absence

**Chosen:** Backend adds `taskDescription` and `subtasks` to `agent_trace_start`

**Rationale:**
- These fields are already expected by frontend components
- Backend demo should match production agent behavior
- Cleaner than adding null checks throughout frontend

### Decision 3: Global timeline implementation approach

**Chosen:** Extract and merge steps from all traces in CenterPanel

**Rationale:**
- Keeps data in single source of truth (traces Map)
- Simple transformation: flatten all trace.steps arrays and sort by timestamp
- Real-time updates work automatically via Zustand reactivity

**Alternative considered:** Maintain separate global timeline in store
- Would duplicate data
- Requires additional state management

### Decision 4: Reuse ExecutionTimeline vs create new component

**Chosen:** Create new `GlobalTimeline` component that displays steps with agent context

**Rationale:**
- ExecutionTimeline is designed for single-agent view
- Global view needs to show which agent generated each step
- Cleaner separation of concerns

## Risks / Trade-offs

**[Risk]** Field mapping in store could be missed for future message types
→ **Mitigation:** Document the mapping pattern clearly, add type guards

**[Risk]** Global timeline performance with many steps
→ **Mitigation:** Steps are already in memory; sorting is O(n log n) which is acceptable for typical trace sizes

**[Trade-off]** Backend demo changes won't automatically apply to production agents
→ Production agent implementation will need same field additions

## Migration Plan

1. Update backend `demo_trace.py` to send correct field names and missing fields
2. Update `diagnosisStore.ts` to map incoming fields
3. Create `GlobalTimeline` component
4. Update `Investigation.tsx` CenterPanel to use GlobalTimeline
5. Test with demo trace to verify all issues resolved

No rollback needed - changes are additive and backwards compatible.
