# State Management

## Purpose
Hybrid state persistence with in-memory runtime, snapshots, and event sourcing.

## Requirements

### Requirement: Hybrid state persistence
The system SHALL maintain diagnosis state in three layers: in-memory runtime state, periodic snapshots, and complete event stream.

#### Scenario: Runtime state management
- **WHEN** a diagnosis workflow is executing
- **THEN** the system SHALL maintain the complete current state in memory including messages, hypothesis tree, timeline, and confidence

#### Scenario: Snapshot creation
- **WHEN** a workflow node completes successfully
- **THEN** the system SHALL save a state snapshot to the `diagnosis_sessions` table in PostgreSQL

#### Scenario: Event stream recording
- **WHEN** any state change occurs during diagnosis
- **THEN** the system SHALL append an event record to the `diagnosis_events` table with event type, data, timestamp, and sequence number

### Requirement: Event sourcing
The system SHALL record all state changes as immutable events for complete audit trail.

#### Scenario: Event ordering
- **WHEN** multiple events are recorded for a session
- **THEN** each event SHALL have a monotonically increasing sequence number to preserve order

#### Scenario: Event replay
- **WHEN** a diagnosis session needs to be reconstructed
- **THEN** the system SHALL be able to replay all events from the event stream to rebuild the complete state

### Requirement: State recovery
The system SHALL support recovery of diagnosis state after failures.

#### Scenario: Recovery from latest snapshot
- **WHEN** a workflow execution is interrupted
- **THEN** the system SHALL load the most recent snapshot and replay events since that snapshot to restore state

#### Scenario: Full event replay
- **WHEN** no snapshot exists for a session
- **THEN** the system SHALL replay all events from the beginning to reconstruct the state

### Requirement: State query performance
The system SHALL optimize state queries using snapshots to avoid full event replay.

#### Scenario: Current state retrieval
- **WHEN** a client requests the current diagnosis state
- **THEN** the system SHALL return the latest snapshot plus any subsequent events without replaying the entire history

#### Scenario: Historical state query
- **WHEN** a client requests state at a specific point in time
- **THEN** the system SHALL load the nearest prior snapshot and replay events up to the requested timestamp
