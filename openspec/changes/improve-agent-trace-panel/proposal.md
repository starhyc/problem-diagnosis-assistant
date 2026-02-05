## Why

The AgentTracePanel currently lacks key information display and suffers from performance issues during real-time agent execution. Users need to see detailed agent metadata (short IDs, task descriptions, token usage, subtask progress) and the UI becomes sluggish when multiple agents are running simultaneously with frequent WebSocket updates.

## What Changes

- **AgentHierarchyTree enhancements**:
  - Display truncated agent IDs (first 8 characters)
  - Show task descriptions below agent names
  - Display token usage with up/down arrows (↑input ↓output)
  - Show subtask progress counters (e.g., "6/9 subtasks")
  - Add collapse/expand functionality with default folding at level 2+

- **ExecutionTimeline improvements**:
  - Add copy button to goal/task header
  - Improve timestamp formatting (12-hour format with AM/PM)
  - Better visual grouping of execution steps

- **Performance optimizations**:
  - Wrap AgentNode with React.memo to prevent unnecessary re-renders
  - Wrap StepItem with React.memo to prevent unnecessary re-renders
  - Add collapse state management to reduce DOM nodes

## Capabilities

### New Capabilities
- `agent-trace-display`: Enhanced agent trace visualization with detailed metadata, hierarchical navigation, and execution timeline
- `agent-trace-performance`: Performance optimizations for real-time agent trace updates with memoization and lazy rendering

### Modified Capabilities
<!-- No existing capabilities are being modified -->

## Impact

**Affected Components**:
- `src/components/investigation/AgentHierarchyTree.tsx` - UI enhancements and collapse functionality
- `src/components/investigation/ExecutionTimeline.tsx` - Header improvements and memoization
- `src/types/trace.ts` - May need additional fields for task descriptions and subtask counts
- `src/store/diagnosisStore.ts` - Ensure WebSocket messages include new metadata fields

**Dependencies**:
- No new dependencies required
- Uses existing React hooks and Zustand store patterns

**User Experience**:
- More informative agent tree view with collapsible nodes
- Reduced UI lag during high-frequency WebSocket updates
- Better visibility into agent execution details
