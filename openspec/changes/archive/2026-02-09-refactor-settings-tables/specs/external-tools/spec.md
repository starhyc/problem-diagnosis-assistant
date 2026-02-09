## MODIFIED Requirements

### Requirement: Test tool connection
The system SHALL perform real HTTP connection tests to external tool endpoints with timeout and status tracking.

#### Scenario: Test ELK connection
- **WHEN** admin tests ELK tool connection
- **THEN** system performs HTTP GET request to ELK endpoint and returns actual connection status

#### Scenario: Test GitLab connection
- **WHEN** admin tests GitLab tool connection
- **THEN** system performs HTTP GET request to GitLab API and returns actual connection status

#### Scenario: Test Kubernetes connection
- **WHEN** admin tests Kubernetes tool connection
- **THEN** system performs HTTP GET request to K8s API and returns actual connection status

#### Scenario: Test Neo4j connection
- **WHEN** admin tests Neo4j tool connection
- **THEN** system performs HTTP GET request to Neo4j HTTP endpoint and returns actual connection status

#### Scenario: Connection test timeout
- **WHEN** tool endpoint is unreachable
- **THEN** system returns timeout error after 5 seconds

#### Scenario: Connection test success
- **WHEN** tool endpoint responds with HTTP 200-299
- **THEN** system returns success status and updates last_test_at timestamp

#### Scenario: Connection test failure
- **WHEN** tool endpoint responds with HTTP error or connection refused
- **THEN** system returns failure status with error message and updates last_test_status

#### Scenario: Store test results
- **WHEN** connection test completes
- **THEN** system stores last_test_at timestamp and last_test_status in database

## ADDED Requirements

### Requirement: Track connection test history
The system SHALL store connection test results for monitoring and troubleshooting.

#### Scenario: Record successful test
- **WHEN** connection test succeeds
- **THEN** system updates tool record with last_test_at timestamp and last_test_status='success'

#### Scenario: Record failed test
- **WHEN** connection test fails
- **THEN** system updates tool record with last_test_at timestamp and last_test_status='failed'

#### Scenario: Display test history
- **WHEN** admin views tool list
- **THEN** system displays last test timestamp and status for each tool
