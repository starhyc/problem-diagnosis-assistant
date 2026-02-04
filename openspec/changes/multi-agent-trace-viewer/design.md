## Context

The current Investigation page uses a flat message list in `AgentCollaborationPanel` to display agent execution. This works for single-agent scenarios but breaks down when agents orchestrate other agents (plan-agent → sub-agent-1 → sub-sub-agent). Users cannot see execution hierarchy, identify bottlenecks, or understand token consumption patterns.

The RightPanel currently shows topology graphs and hypothesis trees, which are less critical during active diagnosis. We'll repurpose this space for the new Agent Trace System.

**Current Architecture:**
- `diagnosisStore` receives flat `agent_message` WebSocket events
- `AgentCollaborationPanel` renders messages as a linear list
- No parent-child agent relationships tracked
- No granular step-level data (LLM vs tool execution)

**Constraints:**
- Backend will use demo/mock data initially (no real agent instrumentation yet)
- Must maintain WebSocket-based real-time updates
- Should not break existing diagnosis workflow in CenterPanel

## Goals / Non-Goals

**Goals:**
- Display hierarchical agent execution tree with real-time status updates
- Show detailed execution timeline with LLM thinking, tool calls, and sub-agent dispatching
- Display metrics (duration, tokens, cost) at both agent and step levels
- Support agent selection to view individual agent details
- Implement backend demo mode for frontend development

**Non-Goals:**
- Modifying CenterPanel or existing agent collaboration view (keep for backwards compatibility)
- Real backend agent instrumentation (demo data only for now)
- Historical trace replay or persistence
- Trace export or sharing features
- Performance optimization for 100+ agents (optimize later if needed)

## Decisions

### Decision 1: Replace RightPanel tabs with Agent Trace System

**Rationale:** The RightPanel currently shows topology and hypothesis views that are less actionable during active diagnosis. The trace viewer provides more immediate value for debugging multi-agent workflows.

**Alternatives considered:**
- Add fourth tab to CenterPanel → Rejected: CenterPanel already has 3 tabs, adding more creates clutter
- Create new modal/overlay → Rejected: Reduces screen real estate, harder to monitor in real-time
- Keep topology/hypothesis → Rejected: Less useful than execution traces for debugging

**Trade-off:** Users lose quick access to topology/hypothesis views. Mitigation: These could be moved to a separate page or modal if needed later.

### Decision 2: Split RightPanel into two-column layout (tree + timeline)

**Layout:**
```
┌─────────────────────────────────────┐
│  RightPanel (w-96)                  │
├──────────────┬──────────────────────┤
│ Tree (w-40)  │  Timeline (flex-1)   │
│              │                      │
│ ▼ plan-agent │  Metrics Panel       │
│   ├─ sub-1   │  ─────────────       │
│   └─ sub-2   │  Step 1: Task recv   │
│              │  Step 2: LLM think   │
│              │  Step 3: Tool call   │
└──────────────┴──────────────────────┘
```

**Rationale:**
- Tree provides navigation and hierarchy overview
- Timeline shows detailed execution for selected agent
- Side-by-side layout allows monitoring both simultaneously

**Alternatives considered:**
- Stacked layout (tree on top, timeline below) → Rejected: Vertical space is limited, timeline needs more height
- Full-width tree with expandable timeline → Rejected: More clicks to see details

### Decision 3: New WebSocket message types for trace streaming

**New message types:**
- `agent_trace_start`: Agent begins execution
- `agent_trace_step`: Individual execution step (LLM/tool/dispatch)
- `agent_trace_complete`: Agent finishes execution

**Rationale:** Structured events allow frontend to build hierarchy and timeline incrementally. Separating start/step/complete enables real-time updates as execution progresses.

**Alternatives considered:**
- Extend existing `agent_message` type → Rejected: Too much overloading, harder to parse
- Single `agent_trace` message with full data → Rejected: Can't stream updates in real-time
- Polling REST API → Rejected: WebSocket already established, polling adds latency

**Data structure:**
```typescript
// agent_trace_start
{
  type: 'agent_trace_start',
  data: {
    traceId: string,
    agentId: string,
    agentName: string,
    parentId: string | null,
    startTime: string
  }
}

// agent_trace_step
{
  type: 'agent_trace_step',
  data: {
    traceId: string,
    agentId: string,
    stepId: string,
    stepType: 'task_received' | 'llm_thinking' | 'tool_call' | 'agent_dispatch',
    timestamp: string,
    duration?: number,
    // Step-specific fields
    content?: string,
    toolName?: string,
    toolInput?: any,
    toolOutput?: any,
    status?: 'success' | 'failed',
    tokens?: { input: number, output: number },
    cost?: number
  }
}

// agent_trace_complete
{
  type: 'agent_trace_complete',
  data: {
    traceId: string,
    agentId: string,
    status: 'success' | 'failed',
    endTime: string,
    duration: number,
    totalTokens: { input: number, output: number },
    error?: string
  }
}
```

### Decision 4: Store trace data in diagnosisStore as tree structure

**Rationale:** Store agents as a flat map keyed by agentId, with parentId references. This allows O(1) lookups while maintaining hierarchy through references.

```typescript
interface AgentTrace {
  id: string;
  name: string;
  parentId: string | null;
  status: 'pending' | 'running' | 'success' | 'failed';
  startTime: string;
  endTime?: string;
  duration?: number;
  totalTokens: { input: number; output: number };
  steps: ExecutionStep[];
}

interface ExecutionStep {
  id: string;
  type: 'task_received' | 'llm_thinking' | 'tool_call' | 'agent_dispatch';
  timestamp: string;
  duration?: number;
  // ... step-specific fields
}

// Store structure
{
  traces: Map<string, AgentTrace>,  // agentId -> trace
  selectedAgentId: string | null,
  rootAgentIds: string[]  // for quick access to roots
}
```

**Alternatives considered:**
- Nested tree structure → Rejected: Harder to update individual agents, requires tree traversal
- Array with parent references → Rejected: Map provides faster lookups

### Decision 5: Backend demo mode using setTimeout for realistic delays

**Rationale:** Use `setTimeout` to simulate realistic execution timing (LLM calls take 1-2s, tool calls 0.5-3s). This allows frontend development without waiting for real agent instrumentation.

**Demo scenario:**
```
plan-agent (15s total)
  ├─ sub-agent-1 (3s)
  │   ├─ Step 1: Task received (0s)
  │   ├─ Step 2: LLM thinking (1.5s)
  │   └─ Step 3: Tool call query_db (0.5s)
  └─ sub-agent-2 (5s)
      ├─ Step 1: Task received (0s)
      ├─ Step 2: Tool call check_metrics (1.8s)
      └─ Step 3: LLM thinking (0.9s)
```

**Implementation:** Create a demo endpoint or WebSocket handler that streams these events with delays.

## Risks / Trade-offs

**[Risk] RightPanel width (w-96) may be too narrow for long tool outputs**
→ Mitigation: Use collapsible sections for tool input/output, show truncated preview with "expand" button

**[Risk] Large agent hierarchies (10+ levels) may overflow tree view**
→ Mitigation: Add horizontal scrolling to tree panel, or implement virtual scrolling if needed

**[Risk] High-frequency step updates may cause performance issues**
→ Mitigation: Batch WebSocket messages on backend (send max 10 steps/second), use React.memo on timeline components

**[Risk] Demo data may not reflect real agent behavior**
→ Mitigation: Design demo scenarios with product team input, iterate based on feedback

**[Trade-off] Removing topology/hypothesis tabs**
→ Users lose these views. Mitigation: Can be restored as modal dialogs or moved to separate page if users request them

**[Risk] WebSocket message ordering issues (step arrives before start)**
→ Mitigation: Buffer out-of-order messages in frontend, apply them when parent agent exists

## Migration Plan

**Phase 1: Frontend structure (no backend changes)**
1. Create new components: `AgentTracePanel`, `AgentHierarchyTree`, `ExecutionTimeline`
2. Add new types to `src/types/trace.ts`
3. Update `Investigation.tsx` to render new RightPanel
4. Keep existing WebSocket handlers working (no breaking changes yet)

**Phase 2: Backend demo mode**
1. Add new WebSocket message handlers for `agent_trace_*` types
2. Create demo trace generator that simulates multi-agent execution
3. Wire up demo mode to trigger on diagnosis start

**Phase 3: Frontend integration**
1. Update `diagnosisStore` to handle new message types
2. Build trace tree from incoming messages
3. Implement agent selection and timeline rendering
4. Test with demo backend

**Phase 4: Polish**
1. Add loading states, error handling
2. Optimize rendering performance
3. Add visual polish (animations, colors, icons)

**Rollback strategy:** If issues arise, revert RightPanel to show topology/hypothesis tabs. New WebSocket messages are additive (don't break existing `agent_message` flow).

## Open Questions

1. Should we persist traces to backend database for historical analysis? (Out of scope for now, but worth considering)
2. What's the maximum expected agent hierarchy depth? (Affects tree UI design)
3. Should tool outputs be syntax-highlighted based on content type (JSON, logs, etc.)? (Nice-to-have)
4. Do we need trace filtering (e.g., show only failed agents, only tool calls)? (Can add later based on feedback)
