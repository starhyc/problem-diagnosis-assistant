## 1. Update Type Definitions

- [ ] 1.1 Add `taskDescription?: string` field to AgentTrace type in src/types/trace.ts
- [ ] 1.2 Add `subtasks?: { completed: number; total: number }` field to AgentTrace type in src/types/trace.ts

## 2. Enhance AgentHierarchyTree Component

- [ ] 2.1 Add collapse state with `useState(level >= 2)` in AgentNode component
- [ ] 2.2 Add chevron button for collapse/expand with stopPropagation
- [ ] 2.3 Conditionally render children based on collapse state
- [ ] 2.4 Display truncated agent ID (first 8 characters) below agent name
- [ ] 2.5 Display task description below agent name when available
- [ ] 2.6 Display token usage with ↑/↓ arrows format
- [ ] 2.7 Display subtask progress counter when subtasks exist
- [ ] 2.8 Wrap AgentNode with React.memo comparing trace.status, trace.duration, and selectedAgentId

## 3. Improve ExecutionTimeline Component

- [ ] 3.1 Add copy button to MetricsPanel header
- [ ] 3.2 Implement clipboard copy using navigator.clipboard.writeText()
- [ ] 3.3 Update formatTimestamp to use 12-hour format with AM/PM
- [ ] 3.4 Wrap StepItem with React.memo comparing step object reference

## 4. Testing and Verification

- [ ] 4.1 Test collapse/expand functionality with nested agents
- [ ] 4.2 Verify React.memo prevents unnecessary re-renders during WebSocket updates
- [ ] 4.3 Test UI displays correctly when taskDescription and subtasks are missing
- [ ] 4.4 Verify copy button works and copies correct text
- [ ] 4.5 Verify timestamp format displays as "HH:MM AM/PM"
