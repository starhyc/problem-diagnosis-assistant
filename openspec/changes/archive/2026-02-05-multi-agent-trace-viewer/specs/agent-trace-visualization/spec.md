## ADDED Requirements

### Requirement: Display hierarchical agent execution tree
The system SHALL display a hierarchical tree view of agent execution showing parent-child relationships between agents with real-time status indicators.

#### Scenario: Root agent with child agents
- **WHEN** a plan-agent spawns sub-agent-1 and sub-agent-2
- **THEN** the tree displays plan-agent as root with two child nodes showing sub-agent-1 and sub-agent-2

#### Scenario: Multi-level agent hierarchy
- **WHEN** sub-agent-1 spawns sub-sub-agent
- **THEN** the tree displays three levels with proper indentation and connection lines

#### Scenario: Real-time status updates
- **WHEN** an agent transitions from running to success or failed
- **THEN** the tree node updates its status indicator (color and icon) immediately

### Requirement: Show agent execution metrics
The system SHALL display core execution metrics for each agent including status, total duration, input tokens, and output tokens.

#### Scenario: Display metrics panel
- **WHEN** user selects an agent in the hierarchy tree
- **THEN** a metrics panel displays status, total duration, input token count, and output token count

#### Scenario: Running agent metrics
- **WHEN** an agent is currently running
- **THEN** the duration updates in real-time and token counts show current values

### Requirement: Display detailed execution timeline
The system SHALL display a step-by-step execution timeline showing LLM thinking, tool calls, and sub-agent dispatching with timing and status information.

#### Scenario: LLM reasoning step
- **WHEN** an agent performs LLM reasoning
- **THEN** the timeline displays a step showing timestamp, "LLM 请求/思考" label, thinking content, duration, and token cost

#### Scenario: Tool invocation step
- **WHEN** an agent calls a tool
- **THEN** the timeline displays a step showing timestamp, tool name, input parameters, output results, success/failure status, and duration

#### Scenario: Sub-agent dispatch step
- **WHEN** an agent dispatches a sub-agent
- **THEN** the timeline displays a step showing timestamp, target agent name, and task description

#### Scenario: Task reception step
- **WHEN** an agent receives a task
- **THEN** the timeline displays a step showing timestamp, "接收任务" label, and input description

### Requirement: Support agent selection and navigation
The system SHALL allow users to select agents in the hierarchy tree to view their detailed execution timeline.

#### Scenario: Select agent in tree
- **WHEN** user clicks on an agent node in the hierarchy tree
- **THEN** the right panel displays that agent's detailed execution timeline and metrics

#### Scenario: Visual selection indicator
- **WHEN** an agent is selected
- **THEN** the tree node displays a visual indicator (checkmark or highlight) showing it is selected

### Requirement: Display execution step timestamps
The system SHALL display timestamps for each execution step in HH:MM:SS format.

#### Scenario: Step timestamp display
- **WHEN** an execution step is displayed in the timeline
- **THEN** the timestamp shows in HH:MM:SS format at the start of the step

### Requirement: Distinguish step types visually
The system SHALL use distinct visual indicators (colors and icons) for different step types including task reception, LLM thinking, tool calls, and sub-agent dispatch.

#### Scenario: Step type indicators
- **WHEN** the timeline displays multiple step types
- **THEN** each step type uses a unique color indicator (green for task reception, blue for LLM, orange for tools, purple for dispatch)
