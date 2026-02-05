## 1. Fix AgentHierarchyTree Re-rendering

- [x] 1.1 Remove React.memo wrapper from AgentNode component in AgentHierarchyTree.tsx
- [x] 1.2 Remove memo comparison function (lines 110-113) from AgentNode

## 2. Update Collapse Behavior

- [x] 2.1 Modify collapsed state initialization to check agent status in AgentHierarchyTree.tsx
- [x] 2.2 Change default collapse logic: expanded when status === 'running', collapsed (level >= 2) when status === 'success' or 'failed'

## 3. Add Real-time Metrics to ExecutionTimeline

- [x] 3.1 Create helper function to calculate elapsed time from trace.startTime to Date.now()
- [x] 3.2 Create helper function to accumulate tokens by summing step.tokens from trace.steps array
- [x] 3.3 Add useMemo to cache token accumulation calculation
- [x] 3.4 Update MetricsPanel to use calculated elapsed time when agent is running, fall back to trace.duration when completed
- [x] 3.5 Update MetricsPanel to use accumulated tokens when agent is running, fall back to trace.totalTokens when completed

## 4. Add Elapsed Time Auto-update

- [x] 4.1 Add React state for triggering elapsed time updates in ExecutionTimeline
- [x] 4.2 Add useEffect with setInterval to update elapsed time every 1 second when agent status is 'running'
- [x] 4.3 Clear interval on component unmount and when agent status changes to 'success' or 'failed'

## 5. Testing

- [ ] 5.1 Verify task descriptions appear immediately when agent_trace_start arrives
- [ ] 5.2 Verify sub-agents are visible in real-time during execution (all levels expanded)
- [ ] 5.3 Verify elapsed time updates every second during execution
- [ ] 5.4 Verify accumulated tokens update as steps arrive
- [ ] 5.5 Verify nodes collapse to level >= 2 after agent completion
- [ ] 5.6 Verify final metrics (duration, totalTokens) display correctly after completion
