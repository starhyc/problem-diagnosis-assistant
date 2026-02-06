# Realtime Communication

## Purpose
WebSocket and Redis Pub/Sub integration for real-time diagnosis updates across multiple instances.

## Requirements

### Requirement: WebSocket connection management
The system SHALL maintain WebSocket connections for real-time diagnosis updates.

#### Scenario: Client connection
- **WHEN** a client establishes a WebSocket connection
- **THEN** the system SHALL accept the connection and assign a unique connection ID

#### Scenario: Connection heartbeat
- **WHEN** a WebSocket connection is idle for more than 30 seconds
- **THEN** the system SHALL send a ping message to keep the connection alive

#### Scenario: Connection cleanup
- **WHEN** a WebSocket connection is closed
- **THEN** the system SHALL unsubscribe from all Redis Pub/Sub channels for that connection

### Requirement: Redis Pub/Sub integration
The system SHALL use Redis Pub/Sub to broadcast diagnosis events from workers to WebSocket handlers.

#### Scenario: Event publication
- **WHEN** a Celery worker generates a diagnosis event
- **THEN** it SHALL publish the event to a Redis channel named `diagnosis:{session_id}`

#### Scenario: Event subscription
- **WHEN** a WebSocket handler receives a diagnosis start request
- **THEN** it SHALL subscribe to the Redis channel `diagnosis:{session_id}` and forward all events to the client

#### Scenario: Multi-instance support
- **WHEN** multiple FastAPI instances are running
- **THEN** each instance SHALL independently subscribe to Redis channels and forward events to its connected clients

### Requirement: Event message types
The system SHALL support multiple event message types for different diagnosis updates.

#### Scenario: Agent message event
- **WHEN** an agent produces output
- **THEN** the system SHALL publish an `agent_message` event with agent ID, timestamp, content, and message type

#### Scenario: Timeline update event
- **WHEN** a workflow node completes
- **THEN** the system SHALL publish a `timeline_update` event with the updated timeline steps

#### Scenario: Hypothesis update event
- **WHEN** the hypothesis tree is modified
- **THEN** the system SHALL publish a `hypothesis_update` event with the updated tree structure

#### Scenario: Confidence update event
- **WHEN** the diagnosis confidence score changes
- **THEN** the system SHALL publish a `confidence_update` event with the new confidence value

#### Scenario: Action proposal event
- **WHEN** the system generates a recommended action
- **THEN** the system SHALL publish an `action_proposal` event with action details and risk level

### Requirement: Connection recovery
The system SHALL support reconnection and event replay for disconnected clients.

#### Scenario: Client reconnection
- **WHEN** a client reconnects with a valid session ID
- **THEN** the system SHALL resubscribe to the diagnosis channel and resume event streaming

#### Scenario: Missed event replay
- **WHEN** a client reconnects after missing events
- **THEN** the system SHALL retrieve missed events from the database and replay them in order
