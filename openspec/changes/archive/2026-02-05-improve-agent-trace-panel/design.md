## Context

The AgentTracePanel displays real-time agent execution traces with a hierarchical tree (AgentHierarchyTree) and detailed timeline (ExecutionTimeline). Currently, the UI lacks essential metadata display and suffers from performance issues during high-frequency WebSocket updates. With up to 10 agents, 5 levels of nesting, 100 steps per agent, and 3 agents running simultaneously, the current implementation causes unnecessary re-renders across all components when any single agent updates.

Current implementation uses recursive rendering without memoization, causing the entire tree and timeline to re-render on every WebSocket message (3-6 updates/second during active diagnosis).

## Goals / Non-Goals

**Goals:**
- Display comprehensive agent metadata (short IDs, task descriptions, token usage, subtask progress)
- Add collapsible tree nodes to manage visual complexity
- Eliminate unnecessary re-renders using React.memo
- Improve timestamp formatting and add clipboard copy functionality
- Maintain existing data flow through Zustand store and WebSocket

**Non-Goals:**
- Virtual scrolling (scale doesn't justify complexity)
- Pagination or limiting display (would hide useful information)
- Restructuring Zustand store or WebSocket message format
- Adding new external dependencies

## Decisions

### Decision 1: Use React.memo with custom comparison functions

**Rationale:** At the current scale (10 agents, 100 steps), the bottleneck is re-render frequency, not DOM node count. React.memo prevents components from re-rendering when their props haven't changed.

**Implementation:**
- Wrap `AgentNode` with `React.memo` comparing `trace.status`, `trace.duration`, and `selectedAgentId`
- Wrap `StepItem` with `React.memo` comparing the `step` object reference
- Use shallow equality checks (strict `===`) for performance

**Alternatives considered:**
- useMemo for child arrays: Doesn't prevent component re-renders, only memoizes values
- Restructure Zustand store with selectors: Higher complexity, minimal benefit at this scale
- Web Workers: Overkill for 10 agents and 100 steps

### Decision 2: Component-local collapse state with default folding at level 2+

**Rationale:** Collapse state is UI-only concern, doesn't need global state management. Default folding reduces initial visual clutter while keeping root and first-level agents visible.

**Implementation:**
- Add `useState` for collapse state in each `AgentNode`
- Initialize with `useState(level >= 2)` to collapse nodes at level 2 and deeper
- Conditionally render children: `{!collapsed && children.map(...)}`
- Add chevron button with `stopPropagation` to prevent triggering agent selection

**Alternatives considered:**
- Global collapse state in Zustand: Unnecessary complexity for UI-only state
- Persist collapse state: No user requirement for persistence across sessions

### Decision 3: Extend AgentTrace type for new metadata fields

**Rationale:** Backend WebSocket messages need to include task descriptions and subtask counts. Frontend types must match.

**Implementation:**
- Add optional fields to `AgentTrace` type:
  - `taskDescription?: string`
  - `subtasks?: { completed: number; total: number }`
- Display conditionally based on field presence
- Truncate agent ID using `trace.id.substring(0, 8)`

**Alternatives considered:**
- Compute metadata in frontend: Not possible, data comes from backend agent execution
- Separate metadata object: Unnecessary indirection, fields belong on AgentTrace

### Decision 4: Use Clipboard API for copy functionality

**Rationale:** Modern browsers support `navigator.clipboard.writeText()` natively. No dependencies needed.

**Implementation:**
- Add copy button in ExecutionTimeline header
- Call `navigator.clipboard.writeText(trace.taskDescription || trace.name)`
- Show temporary success indicator (optional enhancement)

**Alternatives considered:**
- execCommand('copy'): Deprecated API
- External clipboard library: Unnecessary for simple text copy

### Decision 5: Format timestamps using toLocaleTimeString with 12-hour format

**Rationale:** Current implementation uses default locale format. Explicit 12-hour format with AM/PM improves consistency.

**Implementation:**
- Change `formatTimestamp` to use `toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })`
- Output format: "2:54 PM"

## Risks / Trade-offs

**[Risk]** Backend doesn't send taskDescription or subtasks fields
→ **Mitigation:** Display fields conditionally. If missing, UI gracefully omits them. Backend changes are independent.

**[Risk]** React.memo comparison logic too strict, misses updates
→ **Mitigation:** Compare only fields that affect rendering. Test with real WebSocket updates to verify correctness.

**[Risk]** Collapse state lost when parent re-renders
→ **Mitigation:** React preserves component state by key. Ensure `key={trace.id}` is stable across renders.

**[Trade-off]** Memoization adds comparison overhead
→ **Acceptable:** Comparison cost is negligible vs. re-rendering 100+ components. Net performance gain.

**[Trade-off]** Collapsed nodes hide information
→ **Acceptable:** Users can expand nodes on demand. Default folding improves initial UX without losing access.
