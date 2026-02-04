## ADDED Requirements

### Requirement: Stream agent trace start events
The system SHALL send a WebSocket message when an agent execution begins, including agent ID, name, parent ID, and start timestamp.

#### Scenario: Root agent starts
- **WHEN** a root agent begins execution
- **THEN** a WebSocket message with type "agent_trace_start" is sent with agent ID, name, null parent ID, and start timestamp

#### Scenario: Child agent starts
- **WHEN** a child agent begins execution
- **THEN** a WebSocket message with type "agent_trace_start" is sent with agent ID, name, parent agent ID, and start timestamp

### Requirement: Stream agent execution step events
The system SHALL send WebSocket messages for each execution step including LLM thinking, tool calls, and sub-agent dispatching with timing and status information.

#### Scenario: LLM thinking step
- **WHEN** an agent performs LLM reasoning
- **THEN** a WebSocket message with type "agent_trace_step" is sent containing step type "llm_thinking", timestamp, content, duration, input tokens, output tokens, and cost

#### Scenario: Tool invocation step
- **WHEN** an agent invokes a tool
- **THEN** a WebSocket message with type "agent_trace_step" is sent containing step type "tool_call", timestamp, tool name, input parameters, output result, success/failure status, and duration

#### Scenario: Sub-agent dispatch step
- **WHEN** an agent dispatches a sub-agent
- **THEN** a WebSocket message with type "agent_trace_step" is sent containing step type "agent_dispatch", timestamp, target agent ID, and task description

#### Scenario: Task reception step
- **WHEN** an agent receives a task
- **THEN** a WebSocket message with type "agent_trace_step" is sent containing step type "task_received", timestamp, and input description

### Requirement: Stream agent completion events
The system SHALL send a WebSocket message when an agent execution completes, including final status, end timestamp, and total metrics.

#### Scenario: Successful agent completion
- **WHEN** an agent completes successfully
- **THEN** a WebSocket message with type "agent_trace_complete" is sent with agent ID, status "success", end timestamp, total duration, total input tokens, and total output tokens

#### Scenario: Failed agent completion
- **WHEN** an agent execution fails
- **THEN** a WebSocket message with type "agent_trace_complete" is sent with agent ID, status "failed", end timestamp, error message, and partial metrics

### Requirement: Maintain agent hierarchy relationships
The system SHALL track and communicate parent-child relationships between agents through parent ID references.

#### Scenario: Multi-level hierarchy
- **WHEN** plan-agent spawns sub-agent-1 which spawns sub-sub-agent
- **THEN** each agent's trace start event includes the correct parent ID forming a complete hierarchy chain

### Requirement: Support demo mode for backend
The system SHALL provide demo/mock implementations of trace streaming for frontend development without requiring full backend agent execution.

#### Scenario: Demo trace data
- **WHEN** backend is in demo mode
- **THEN** it streams realistic mock trace events simulating multi-agent execution with timing delays and varied step types
