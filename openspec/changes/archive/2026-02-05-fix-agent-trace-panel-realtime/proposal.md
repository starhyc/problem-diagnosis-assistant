## Why

The AgentTracePanel currently provides poor real-time visibility during agent execution. Users cannot see task descriptions, sub-agent spawning, or accumulated metrics until after agents complete, making it difficult to monitor and understand ongoing diagnosis workflows.

## What Changes

- Fix AgentHierarchyTree component re-rendering to display task descriptions and token updates in real-time as data arrives
- Change default collapse behavior to keep all agent nodes expanded during active execution for better visibility of sub-agent spawning
- Add real-time metric calculation in ExecutionTimeline to show elapsed time and accumulated tokens during execution instead of only after completion

## Capabilities

### New Capabilities

- `agent-trace-realtime-metrics`: Real-time calculation and display of execution metrics (elapsed time, accumulated tokens) during agent execution

### Modified Capabilities

- `agent-trace-display`: Update requirements for component re-rendering behavior and default collapse state during active execution

## Impact

**Frontend Components:**
- `src/components/investigation/AgentHierarchyTree.tsx` - Fix memo comparison and collapse logic
- `src/components/investigation/ExecutionTimeline.tsx` - Add real-time metric calculation
- `src/store/diagnosisStore.ts` - May need to accumulate tokens as steps arrive

**No Breaking Changes:** All changes are internal UI improvements with no API or data structure changes.
