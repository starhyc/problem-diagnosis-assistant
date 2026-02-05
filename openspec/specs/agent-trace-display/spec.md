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

### Requirement: Collapsible tree nodes
The AgentHierarchyTree SHALL support collapsing and expanding tree nodes to manage visual complexity.

#### Scenario: Default collapse state
- **WHEN** the agent hierarchy tree is rendered
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
