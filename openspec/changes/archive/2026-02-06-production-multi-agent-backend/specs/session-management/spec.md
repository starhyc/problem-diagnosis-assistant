## ADDED Requirements

### Requirement: Redis session storage
The system SHALL store all WebSocket session data in Redis for multi-instance deployment support.

#### Scenario: Session creation
- **WHEN** a WebSocket client connects
- **THEN** the system SHALL create a session record in Redis with a unique session ID and TTL of 1 hour

#### Scenario: Session data persistence
- **WHEN** session data is updated
- **THEN** the system SHALL persist the changes to Redis with an updated TTL

#### Scenario: Session expiration
- **WHEN** a session is inactive for more than 1 hour
- **THEN** Redis SHALL automatically expire and remove the session data

### Requirement: Session data structure
The system SHALL store session metadata including client ID, user ID, diagnosis ID, connection timestamp, and last activity timestamp.

#### Scenario: Session metadata storage
- **WHEN** a session is created
- **THEN** it SHALL include client_id, user_id, diagnosis_id, connected_at, and last_activity_at fields

#### Scenario: Session metadata retrieval
- **WHEN** a session is accessed by session ID
- **THEN** the system SHALL return all session metadata from Redis

### Requirement: Multi-instance session sharing
The system SHALL enable session access across multiple FastAPI instances.

#### Scenario: Cross-instance session access
- **WHEN** a client reconnects to a different FastAPI instance
- **THEN** the new instance SHALL retrieve the session data from Redis and resume the connection

#### Scenario: Session lock for updates
- **WHEN** multiple instances attempt to update the same session simultaneously
- **THEN** the system SHALL use Redis locks to prevent race conditions

### Requirement: Session cleanup
The system SHALL clean up expired sessions and associated resources.

#### Scenario: Automatic cleanup
- **WHEN** a session expires in Redis
- **THEN** the system SHALL unsubscribe from associated Redis Pub/Sub channels

#### Scenario: Manual session termination
- **WHEN** a user explicitly logs out or closes the connection
- **THEN** the system SHALL immediately delete the session from Redis
