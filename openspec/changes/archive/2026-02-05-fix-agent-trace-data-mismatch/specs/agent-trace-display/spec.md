# Agent Trace Display (Delta)

## MODIFIED Requirements

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

## ADDED Requirements

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
