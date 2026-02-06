## ADDED Requirements

### Requirement: Event-driven agent communication
The system SHALL use an event-driven architecture for agent communication instead of direct message passing.

#### Scenario: Event publication
- **WHEN** an agent produces output or completes a task
- **THEN** it SHALL publish an event to the event bus with event type, agent ID, timestamp, and payload

#### Scenario: Event subscription
- **WHEN** an agent needs to react to other agents' outputs
- **THEN** it SHALL subscribe to relevant event types and receive notifications

### Requirement: Structured event types
The system SHALL define structured event types for agent communication.

#### Scenario: Agent output event
- **WHEN** an agent produces analysis results
- **THEN** it SHALL publish an `agent_output` event with agent_id, output_type, content, and metadata

#### Scenario: Agent request event
- **WHEN** an agent needs another agent to perform a task
- **THEN** it SHALL publish an `agent_request` event with target_agent_id, task_type, and parameters

#### Scenario: Agent error event
- **WHEN** an agent encounters an error
- **THEN** it SHALL publish an `agent_error` event with error_type, error_message, and stack_trace

### Requirement: Event ordering and causality
The system SHALL maintain event ordering and causality relationships.

#### Scenario: Event sequence numbers
- **WHEN** events are published
- **THEN** each event SHALL have a monotonically increasing sequence number within its session

#### Scenario: Causal relationships
- **WHEN** an event is triggered by another event
- **THEN** it SHALL include the parent event ID to maintain causality chain

### Requirement: Event persistence
The system SHALL persist all agent communication events for audit and replay.

#### Scenario: Event storage
- **WHEN** an event is published
- **THEN** it SHALL be stored in the `diagnosis_events` table with full event data

#### Scenario: Event replay
- **WHEN** debugging or analyzing a diagnosis session
- **THEN** the system SHALL be able to replay all agent communication events in order

### Requirement: Event filtering and routing
The system SHALL support event filtering and routing based on event types and agent roles.

#### Scenario: Event type filtering
- **WHEN** an agent subscribes to events
- **THEN** it SHALL only receive events matching its subscribed event types

#### Scenario: Agent role-based routing
- **WHEN** an event is published with a target agent role
- **THEN** the system SHALL route the event only to agents with that role
