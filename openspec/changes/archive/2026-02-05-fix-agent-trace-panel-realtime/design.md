## Context

The AgentTracePanel displays agent execution traces through two main components: AgentHierarchyTree (left panel showing agent hierarchy) and ExecutionTimeline (right panel showing execution steps). Currently, these components have three issues preventing real-time visibility:

1. **Stale component rendering**: AgentNode uses React.memo with incomplete comparison, preventing re-renders when taskDescription or totalTokens update
2. **Hidden sub-agents**: Default collapse state (`level >= 2`) hides sub-agent spawning during execution
3. **Delayed metrics**: ExecutionTimeline only shows duration and totalTokens after agent_trace_complete, not during execution

All necessary data already flows through WebSocket (agent_trace_start includes taskDescription, agent_trace_step includes per-step tokens and duration). The issue is purely display logic.

## Goals / Non-Goals

**Goals:**
- Display task descriptions immediately when agent_trace_start arrives
- Show sub-agents spawning in real-time by keeping nodes expanded during execution
- Calculate and display elapsed time and accumulated tokens as steps arrive

**Non-Goals:**
- Changing WebSocket message structure or backend behavior
- Modifying AgentTrace data model
- Adding new WebSocket message types
- Performance optimization beyond fixing unnecessary re-render blocking

## Decisions

### Decision 1: Fix memo comparison vs remove memo entirely

**Chosen**: Remove memo entirely from AgentNode

**Rationale**:
- Current memo comparison (line 110-113) only checks status, duration, and selectedAgentId
- Would need to add deep comparison of taskDescription, totalTokens, steps array, and subtasks
- Deep comparison of frequently-updating arrays (steps) defeats memo purpose
- AgentHierarchyTree updates are already scoped to individual traces, not expensive to re-render
- Simpler code without premature optimization

**Alternative considered**: Add comprehensive memo comparison including all fields
- Rejected: Complex deep comparison logic, harder to maintain, marginal performance benefit

### Decision 2: Collapse behavior - conditional vs always expanded

**Chosen**: Conditional collapse based on agent status

**Rationale**:
- During execution (status === 'running'), keep all levels expanded for visibility
- After completion (status === 'success' | 'failed'), collapse level >= 2 to reduce clutter
- Balances real-time monitoring needs with post-execution readability
- Users can still manually toggle collapse state

**Alternative considered**: Always keep all levels expanded
- Rejected: Large agent trees become unwieldy after completion

### Decision 3: Real-time metrics - store accumulation vs calculate on render

**Chosen**: Calculate on render from steps array

**Rationale**:
- Elapsed time: Calculate from `trace.startTime` to `Date.now()` during rendering
- Accumulated tokens: Sum `step.tokens.input/output` from all steps during rendering
- No store changes needed, keeps state management simple
- Calculation is cheap (small arrays, simple arithmetic)
- Falls back to trace.duration and trace.totalTokens when available (after completion)

**Alternative considered**: Accumulate in diagnosisStore on each agent_trace_step
- Rejected: Adds complexity to store, duplicates data already in steps array

### Decision 4: Update frequency for elapsed time

**Chosen**: Use React state + setInterval for 1-second updates

**Rationale**:
- ExecutionTimeline already has local state for UI concerns
- 1-second granularity sufficient for monitoring (matches backend duration precision)
- Cleanup interval on unmount or when agent completes
- Minimal re-renders (only MetricsPanel, not entire timeline)

**Alternative considered**: Use Zustand store with global interval
- Rejected: Overkill for UI-only concern, couples display logic to state management

## Risks / Trade-offs

**[Risk]** Removing memo may cause more frequent re-renders of AgentNode
→ **Mitigation**: AgentHierarchyTree already scoped to individual traces. If performance issues arise, can add back memo with proper deep comparison.

**[Risk]** Calculating metrics on every render could be expensive for large step arrays
→ **Mitigation**: Use useMemo to cache calculations. Most agents have < 50 steps. Can optimize if needed.

**[Risk]** Elapsed time updates every second may cause visual jitter
→ **Mitigation**: Only update when agent is running. Stop interval on completion. Format consistently (e.g., "2.3s" not "2.345s").

**[Trade-off]** Always-expanded nodes during execution may make large trees harder to navigate
→ **Accepted**: Real-time visibility is the primary goal. Users can manually collapse if needed.
