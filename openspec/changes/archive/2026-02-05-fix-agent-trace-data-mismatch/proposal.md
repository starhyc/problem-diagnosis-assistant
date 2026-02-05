## Why

The diagnosis workbench has data structure mismatches between backend WebSocket messages and frontend components, causing incomplete display and "unknown step type" errors. The backend sends `stepType`/`stepId` but frontend expects `type`/`id`, and CenterPanel displays outdated data instead of real-time agent execution flow.

## What Changes

- Fix field name mismatches in WebSocket message handling (`stepType` → `type`, `stepId` → `id`)
- Add missing fields to `agent_trace_start` message (`taskDescription`, `subtasks`)
- Replace CenterPanel data source from old `currentCase.messages` to real-time trace data
- Create global timeline view showing all agent steps in chronological order

## Capabilities

### New Capabilities
- `global-agent-timeline`: Display all agent execution steps across all agents in chronological order in CenterPanel

### Modified Capabilities
- `agent-trace-display`: Fix data structure mismatches and add missing fields for proper agent trace visualization

## Impact

**Frontend:**
- `src/store/diagnosisStore.ts`: Map WebSocket field names to match frontend types
- `src/pages/Investigation.tsx`: Update CenterPanel to use trace data instead of old messages
- `src/components/investigation/`: May need new component for global timeline view

**Backend:**
- `server/app/services/demo_trace.py`: Add missing fields and fix field naming in WebSocket messages
