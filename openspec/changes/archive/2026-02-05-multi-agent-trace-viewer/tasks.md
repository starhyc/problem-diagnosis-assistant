## 1. Type Definitions

- [x] 1.1 Create `src/types/trace.ts` with AgentTrace, ExecutionStep, TraceMetrics, and StepType types
- [x] 1.2 Add WebSocket message types for agent_trace_start, agent_trace_step, agent_trace_complete to `src/lib/websocket.ts`

## 2. Store Updates

- [x] 2.1 Add trace state to diagnosisStore (traces Map, selectedAgentId, rootAgentIds)
- [x] 2.2 Implement WebSocket message handlers for agent_trace_start in diagnosisStore
- [x] 2.3 Implement WebSocket message handlers for agent_trace_step in diagnosisStore
- [x] 2.4 Implement WebSocket message handlers for agent_trace_complete in diagnosisStore
- [x] 2.5 Add selectAgent action to diagnosisStore
- [x] 2.6 Add helper functions to build agent hierarchy from flat trace map

## 3. Agent Hierarchy Tree Component

- [x] 3.1 Create `src/components/investigation/AgentHierarchyTree.tsx` component
- [x] 3.2 Implement recursive tree rendering with parent-child relationships
- [x] 3.3 Add status indicators (colors and icons) for pending/running/success/failed states
- [x] 3.4 Implement agent selection on click
- [x] 3.5 Add visual selection indicator (checkmark or highlight)
- [x] 3.6 Display agent duration next to each node

## 4. Execution Timeline Component

- [x] 4.1 Create `src/components/investigation/ExecutionTimeline.tsx` component
- [x] 4.2 Implement metrics panel showing status, duration, input/output tokens
- [x] 4.3 Create step rendering for task_received type with timestamp and input
- [x] 4.4 Create step rendering for llm_thinking type with content, duration, tokens, cost
- [x] 4.5 Create step rendering for tool_call type with tool name, parameters, results, status, duration
- [x] 4.6 Create step rendering for agent_dispatch type with target agent and task description
- [x] 4.7 Add color-coded step type indicators (green/blue/orange/purple)
- [x] 4.8 Format timestamps as HH:MM:SS
- [x] 4.9 Add collapsible sections for long tool input/output

## 5. Agent Trace Panel Component

- [x] 5.1 Create `src/components/investigation/AgentTracePanel.tsx` as container component
- [x] 5.2 Implement two-column layout (tree on left, timeline on right)
- [x] 5.3 Connect to diagnosisStore for trace data and selected agent
- [x] 5.4 Handle empty state when no traces exist
- [x] 5.5 Handle loading state when agent is running

## 6. Investigation Page Integration

- [x] 6.1 Update `src/pages/Investigation.tsx` RightPanel to use AgentTracePanel
- [x] 6.2 Remove or comment out topology/hypothesis tabs from RightPanel
- [x] 6.3 Update RightPanel props to pass trace data instead of topology/hypothesis data

## 7. Backend Demo Mode

- [x] 7.1 Create demo trace generator in `server/app/services/demo_trace.py`
- [x] 7.2 Implement demo scenario with plan-agent → sub-agent-1 → sub-agent-2 hierarchy
- [x] 7.3 Add realistic timing delays using asyncio.sleep (1-3s for LLM, 0.5-2s for tools)
- [x] 7.4 Create WebSocket handler for streaming demo trace events
- [x] 7.5 Wire demo mode to trigger on diagnosis start in `server/app/api/v1/endpoints/agent.py`
- [x] 7.6 Add demo trace data with varied step types (task, LLM, tool, dispatch)

## 8. Testing and Polish

- [ ] 8.1 Test agent selection and timeline switching
- [ ] 8.2 Test real-time updates as new trace events arrive
- [ ] 8.3 Test multi-level hierarchy rendering (3+ levels deep)
- [ ] 8.4 Test status transitions (pending → running → success/failed)
- [ ] 8.5 Add loading spinners for running agents
- [ ] 8.6 Add error handling for malformed trace messages
- [ ] 8.7 Verify token counts and durations display correctly
- [ ] 8.8 Test with demo backend end-to-end
