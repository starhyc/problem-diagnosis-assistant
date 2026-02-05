# Agent Trace Display

## Purpose
This capability defines how agent execution traces are displayed in the UI, including agent hierarchy visualization, task information, and execution timeline presentation.

## Requirements

### Requirement: Display truncated agent IDs
The AgentHierarchyTree SHALL display agent IDs truncated to the first 8 characters for improved readability.

#### Scenario: Agent ID is displayed in tree
- **WHEN** an agent trace is rendered in the hierarchy tree
- **THEN** the agent ID SHALL be truncated to 8 characters and displayed below the agent name

### Requirement: Display task descriptions
The AgentHierarchyTree SHALL display task descriptions for each agent below the agent name.

#### Scenario: Task description is available
- **WHEN** an agent trace includes a task description
- **THEN** the task description SHALL be displayed below the agent name in the tree

#### Scenario: Task description is missing
- **WHEN** an agent trace does not include a task description
- **THEN** no task description SHALL be displayed

#### Scenario: Task description is provided in agent_trace_start
- **WHEN** backend sends agent_trace_start message with taskDescription field
- **THEN** the taskDescription SHALL be stored in the trace and displayed in the hierarchy tree

### Requirement: Display token usage
The AgentHierarchyTree SHALL display token usage with directional arrows for input and output tokens.

#### Scenario: Token usage is displayed
- **WHEN** an agent trace includes token usage data
- **THEN** the system SHALL display "↑{input} ↓{output}" format showing input and output token counts

### Requirement: Display subtask progress
The AgentHierarchyTree SHALL display subtask progress counters when an agent has subtasks.

#### Scenario: Agent has subtasks
- **WHEN** an agent trace includes subtask information
- **THEN** the system SHALL display "{completed}/{total} subtasks" below the agent information

#### Scenario: Agent has no subtasks
- **WHEN** an agent trace has no subtasks
- **THEN** no subtask counter SHALL be displayed

#### Scenario: Subtasks are provided in agent_trace_start
- **WHEN** backend sends agent_trace_start message with subtasks field containing {completed, total}
- **THEN** the subtasks SHALL be stored in the trace and displayed in the hierarchy tree

### Requirement: Collapsible tree nodes
The AgentHierarchyTree SHALL support collapsing and expanding tree nodes to manage visual complexity, with conditional default state based on agent execution status.

#### Scenario: Default collapse state for running agents
- **WHEN** the agent hierarchy tree is rendered and agents have status 'running'
- **THEN** all nodes SHALL be expanded by default to show real-time sub-agent spawning

#### Scenario: Default collapse state for completed agents
- **WHEN** the agent hierarchy tree is rendered and agents have status 'success' or 'failed'
- **THEN** nodes at level 2 and deeper SHALL be collapsed by default

#### Scenario: User expands node
- **WHEN** user clicks the expand icon on a collapsed node
- **THEN** the node's children SHALL become visible

#### Scenario: User collapses node
- **WHEN** user clicks the collapse icon on an expanded node
- **THEN** the node's children SHALL become hidden

### Requirement: Copy task to clipboard
The ExecutionTimeline SHALL provide a copy button to copy the agent's goal/task to clipboard.

#### Scenario: User copies task
- **WHEN** user clicks the copy button in the timeline header
- **THEN** the agent's task description SHALL be copied to the clipboard

### Requirement: 12-hour timestamp format
The ExecutionTimeline SHALL display timestamps in 12-hour format with AM/PM indicators.

#### Scenario: Timestamp is displayed
- **WHEN** an execution step is rendered
- **THEN** the timestamp SHALL be formatted as "HH:MM AM/PM" (e.g., "02:54 PM")

### Requirement: Map WebSocket field names to frontend types
The diagnosisStore SHALL map incoming WebSocket message field names to match frontend TypeScript interfaces.

#### Scenario: agent_trace_step with stepType field
- **WHEN** backend sends agent_trace_step message with stepType field
- **THEN** the store SHALL map stepType to type field before adding to trace.steps

#### Scenario: agent_trace_step with stepId field
- **WHEN** backend sends agent_trace_step message with stepId field
- **THEN** the store SHALL map stepId to id field before adding to trace.steps

### Requirement: Display all step types correctly
The ExecutionTimeline SHALL display all step types with appropriate labels and styling.

#### Scenario: Step type is recognized
- **WHEN** a step has type field set to task_received, llm_thinking, tool_call, or agent_dispatch
- **THEN** the step SHALL display with the correct label and color coding

#### Scenario: Step type is unknown
- **WHEN** a step has an unrecognized type value
- **THEN** the step SHALL display with "[未知步骤]" label and default styling

### Requirement: Real-time component updates
The AgentHierarchyTree SHALL re-render when agent trace data changes to display updated information in real-time.

#### Scenario: Task description arrives
- **WHEN** an agent trace receives taskDescription field from agent_trace_start message
- **THEN** the AgentHierarchyTree SHALL re-render to display the task description

#### Scenario: Token counts update
- **WHEN** an agent trace's totalTokens field is updated
- **THEN** the AgentHierarchyTree SHALL re-render to display updated token counts

#### Scenario: Agent status changes
- **WHEN** an agent's status field changes value
- **THEN** the AgentHierarchyTree SHALL re-render to reflect the new status

#### Scenario: Duration becomes available
- **WHEN** an agent trace receives duration field from agent_trace_complete message
- **THEN** the AgentHierarchyTree SHALL re-render to display the duration
