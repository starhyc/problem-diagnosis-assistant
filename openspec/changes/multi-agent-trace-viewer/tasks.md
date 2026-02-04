## 1. Type Definitions

- [ ] 1.1 Create `src/types/trace.ts` with AgentTrace, ExecutionStep, TraceMetrics, and StepType types
- [ ] 1.2 Add WebSocket message types for agent_trace_start, agent_trace_step, agent_trace_complete to `src/lib/websocket.ts`

## 2. Store Updates

- [ ] 2.1 Add trace state to diagnosisStore (traces Map, selectedAgentId, rootAgentIds)
- [ ] 2.2 Implement WebSocket message handlers for agent_trace_start in diagnosisStore
- [ ] 2.3 Implement WebSocket message handlers for agent_trace_step in diagnosisStore
- [ ] 2.4 Implement WebSocket message handlers for agent_trace_complete in diagnosisStore
- [ ] 2.5 Add selectAgent action to diagnosisStore
- [ ] 2.6 Add helper functions to build agent hierarchy from flat trace map

## 3. Agent Hierarchy Tree Component

- [ ] 3.1 Create `src/components/investigation/AgentHierarchyTree.tsx` component
- [ ] 3.2 Implement recursive tree rendering with parent-child relationships
- [ ] 3.3 Add status indicators (colors and icons) for pending/running/success/failed states
- [ ] 3.4 Implement agent selection on click
- [ ] 3.5 Add visual selection indicator (checkmark or highlight)
- [ ] 3.6 Display agent duration next to each node

## 4. Execution Timeline Component

- [ ] 4.1 Create `src/components/investigation/ExecutionTimeline.tsx` component
- [ ] 4.2 Implement metrics panel showing status, duration, input/output tokens
- [ ] 4.3 Create step rendering for task_received type with timestamp and input
- [ ] 4.4 Create step rendering for llm_thinking type with content, duration, tokens, cost
- [ ] 4.5 Create step rendering for tool_call type with tool name, parameters, results, status, duration
- [ ] 4.6 Create step rendering for agent_dispatch type with target agent and task description
- [ ] 4.7 Add color-coded step type indicators (green/blue/orange/purple)
- [ ] 4.8 Format timestamps as HH:MM:SS
- [ ] 4.9 Add collapsible sections for long tool input/output

## 5. Agent Trace Panel Component

- [ ] 5.1 Create `src/components/investigation/AgentTracePanel.tsx` as container component
- [ ] 5.2 Implement two-column layout (tree on left, timeline on right)
- [ ] 5.3 Connect to diagnosisStore for trace data and selected agent
- [ ] 5.4 Handle empty state when no traces exist
- [ ] 5.5 Handle loading state when agent is running

## 6. Investigation Page Integration

- [ ] 6.1 Update `src/pages/Investigation.tsx` RightPanel to use AgentTracePanel
- [ ] 6.2 Remove or comment out topology/hypothesis tabs from RightPanel
- [ ] 6.3 Update RightPanel props to pass trace data instead of topology/hypothesis data

## 7. Backend Demo Mode

- [ ] 7.1 Create demo trace generator in `server/app/services/demo_trace.py`
- [ ] 7.2 Implement demo scenario with plan-agent → sub-agent-1 → sub-agent-2 hierarchy
- [ ] 7.3 Add realistic timing delays using asyncio.sleep (1-3s for LLM, 0.5-2s for tools)
- [ ] 7.4 Create WebSocket handler for streaming demo trace events
- [ ] 7.5 Wire demo mode to trigger on diagnosis start in `server/app/api/v1/endpoints/agent.py`
- [ ] 7.6 Add demo trace data with varied step types (task, LLM, tool, dispatch)

## 8. Testing and Polish

- [ ] 8.1 Test agent selection and timeline switching
- [ ] 8.2 Test real-time updates as new trace events arrive
- [ ] 8.3 Test multi-level hierarchy rendering (3+ levels deep)
- [ ] 8.4 Test status transitions (pending → running → success/failed)
- [ ] 8.5 Add loading spinners for running agents
- [ ] 8.6 Add error handling for malformed trace messages
- [ ] 8.7 Verify token counts and durations display correctly
- [ ] 8.8 Test with demo backend end-to-end
