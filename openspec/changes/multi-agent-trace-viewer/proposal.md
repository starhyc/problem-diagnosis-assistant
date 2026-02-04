## Why

The current Investigation page displays agent execution as a flat message list, which doesn't scale for multi-agent orchestration scenarios. When plan-agent calls sub-agent-1, which calls sub-agent-2, and each performs multiple tool calls and LLM reasoning steps, users cannot understand the execution hierarchy, timing, token consumption, or identify bottlenecks. This makes debugging and optimization of multi-agent workflows nearly impossible.

## What Changes

- Replace the current RightPanel topology/hypothesis tabs with a new Agent Trace System
- Add hierarchical agent navigation tree showing parent-child agent relationships with real-time status indicators
- Add detailed execution timeline view showing step-by-step agent execution including:
  - LLM thinking/reasoning steps with token counts and costs
  - Tool invocations with parameters, results, timing, and success/failure status
  - Sub-agent dispatching with task context
  - Core metrics panel showing status, duration, input/output tokens
- Extend WebSocket message types to support rich trace data from backend
- Add new TypeScript types for agent traces, execution steps, and metrics
- Update diagnosisStore to handle hierarchical trace data structure

## Capabilities

### New Capabilities
- `agent-trace-visualization`: Display hierarchical multi-agent execution traces with detailed step-by-step timeline, metrics, and status tracking

### Modified Capabilities
- `real-time-diagnosis`: Extend WebSocket communication to stream hierarchical agent trace data instead of flat messages

## Impact

**Frontend Changes:**
- `src/pages/Investigation.tsx` - RightPanel component replacement
- `src/components/investigation/` - New AgentTracePanel, AgentHierarchyTree, ExecutionTimeline components
- `src/store/diagnosisStore.ts` - New state structure for hierarchical traces
- `src/types/` - New types for AgentTrace, ExecutionStep, TraceMetrics
- `src/lib/websocket.ts` - New message types for trace streaming

**Backend Changes:**
- WebSocket message schema extensions for `agent_trace_start`, `agent_trace_step`, `agent_trace_complete`
- Agent execution instrumentation to capture timing, tokens, tool calls, and hierarchy

**Breaking Changes:**
- **BREAKING**: RightPanel no longer shows topology/hypothesis tabs (moved or removed)
- **BREAKING**: WebSocket `agent_message` type may be deprecated in favor of structured trace events
