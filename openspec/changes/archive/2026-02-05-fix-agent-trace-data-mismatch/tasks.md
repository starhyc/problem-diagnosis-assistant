## 1. Backend - Fix WebSocket Message Fields

- [x] 1.1 Update `demo_trace.py` _send_step to use `id` instead of `stepId`
- [x] 1.2 Update `demo_trace.py` _send_step to use `type` instead of `stepType`
- [x] 1.3 Add `taskDescription` parameter to `demo_trace.py` _send_trace_start
- [x] 1.4 Add `subtasks` parameter to `demo_trace.py` _send_trace_start
- [x] 1.5 Update demo trace generation to include taskDescription for each agent
- [x] 1.6 Update demo trace generation to include subtasks for plan-agent

## 2. Frontend - Store Field Mapping (Fallback)

- [x] 2.1 Add field mapping in diagnosisStore.ts agent_trace_step handler to map stepType→type
- [x] 2.2 Add field mapping in diagnosisStore.ts agent_trace_step handler to map stepId→id

## 3. Frontend - Global Timeline Component

- [x] 3.1 Create GlobalTimeline component in src/components/investigation/
- [x] 3.2 Implement function to extract and merge all steps from traces Map
- [x] 3.3 Sort merged steps by timestamp in ascending order
- [x] 3.4 Display each step with agent name/id context
- [x] 3.5 Reuse step rendering logic from ExecutionTimeline (StepItem component)

## 4. Frontend - Update CenterPanel

- [x] 4.1 Update Investigation.tsx CenterPanel to use GlobalTimeline for agents tab
- [x] 4.2 Remove dependency on currentCase.messages in AgentCollaborationPanel
- [x] 4.3 Pass traces Map to GlobalTimeline component

## 5. Testing

- [ ] 5.1 Start backend and verify WebSocket messages have correct field names
- [ ] 5.2 Verify AgentHierarchyTree displays taskDescription and subtasks
- [ ] 5.3 Verify ExecutionTimeline shows correct step types (no "未知步骤")
- [ ] 5.4 Verify CenterPanel shows real-time global timeline with all agent steps
- [ ] 5.5 Verify steps from multiple agents are interleaved chronologically
