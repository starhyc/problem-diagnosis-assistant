## MODIFIED Requirements

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

## ADDED Requirements

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
