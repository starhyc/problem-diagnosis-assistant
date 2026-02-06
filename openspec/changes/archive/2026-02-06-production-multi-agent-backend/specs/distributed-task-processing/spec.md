## ADDED Requirements

### Requirement: Celery task queue integration
The system SHALL use Celery 5.4+ with Redis as the message broker for distributed task processing.

#### Scenario: Task submission
- **WHEN** a diagnosis request is received via WebSocket
- **THEN** the system SHALL submit a Celery task to the queue and return a task ID immediately

#### Scenario: Worker task execution
- **WHEN** a Celery worker picks up a diagnosis task
- **THEN** it SHALL execute the LangGraph workflow and publish progress events to Redis Pub/Sub

### Requirement: Task retry mechanism
The system SHALL automatically retry failed tasks with exponential backoff.

#### Scenario: Transient failure retry
- **WHEN** a task fails due to a transient error (network timeout, temporary service unavailability)
- **THEN** the system SHALL retry the task up to 3 times with exponential backoff (1s, 2s, 4s)

#### Scenario: Permanent failure
- **WHEN** a task fails with a permanent error (invalid input, configuration error)
- **THEN** the system SHALL not retry and SHALL mark the task as failed immediately

### Requirement: Task timeout handling
The system SHALL enforce timeouts on long-running tasks.

#### Scenario: Task timeout
- **WHEN** a task execution exceeds the configured timeout (default 30 minutes)
- **THEN** the system SHALL cancel the task and publish a timeout event

#### Scenario: Configurable timeout
- **WHEN** a diagnosis task is submitted with a custom timeout
- **THEN** the system SHALL use the custom timeout instead of the default

### Requirement: Task result persistence
The system SHALL persist task results for retrieval after completion.

#### Scenario: Task completion
- **WHEN** a task completes successfully
- **THEN** the system SHALL save the final diagnosis result to PostgreSQL and mark the task as complete

#### Scenario: Task result retrieval
- **WHEN** a client requests task results by task ID
- **THEN** the system SHALL return the persisted result from the database

### Requirement: Worker scaling
The system SHALL support horizontal scaling of Celery workers.

#### Scenario: Multiple workers
- **WHEN** multiple Celery workers are running
- **THEN** tasks SHALL be distributed across workers automatically by the Redis broker

#### Scenario: Worker failure
- **WHEN** a worker crashes during task execution
- **THEN** the task SHALL be requeued and picked up by another worker
