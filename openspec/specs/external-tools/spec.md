## ADDED Requirements

### Requirement: List external tools
The system SHALL return all configured external tool integrations.

#### Scenario: List all tools
- **WHEN** admin requests tool list
- **THEN** system returns all tools with connection status and URLs

#### Scenario: Empty tool list
- **WHEN** no tools are configured
- **THEN** system returns empty array

### Requirement: Test tool connection
The system SHALL allow administrators to test external tool connectivity.

#### Scenario: Test ELK connection
- **WHEN** admin tests ELK tool connection
- **THEN** system attempts connection to ELK endpoint and returns status

#### Scenario: Test GitLab connection
- **WHEN** admin tests GitLab tool connection
- **THEN** system attempts connection to GitLab API and returns status

#### Scenario: Test Kubernetes connection
- **WHEN** admin tests Kubernetes tool connection
- **THEN** system attempts connection to K8s API and returns status

#### Scenario: Test Neo4j connection
- **WHEN** admin tests Neo4j tool connection
- **THEN** system attempts connection to Neo4j database and returns status

#### Scenario: Connection test timeout
- **WHEN** tool endpoint is unreachable
- **THEN** system returns timeout error after 10 seconds

### Requirement: Update tool configuration
The system SHALL allow administrators to update external tool connection settings.

#### Scenario: Update tool URL
- **WHEN** admin updates tool URL
- **THEN** system stores new URL and marks connection as untested

#### Scenario: Enable/disable tool
- **WHEN** admin toggles tool enabled status
- **THEN** system updates enabled flag

### Requirement: Non-admin access restriction
The system SHALL restrict external tool configuration access to administrators only.

#### Scenario: Non-admin attempts to update tool
- **WHEN** non-admin user attempts to update tool configuration
- **THEN** system returns 403 Forbidden error

## REMOVED Requirements

### Requirement: Redline rules management
**Reason**: Not a core requirement for the system, removed to simplify Settings page
**Migration**: Redline rules feature completely removed, no migration needed

### Requirement: Masking rules management
**Reason**: Not a core requirement for the system, removed to simplify Settings page
**Migration**: Masking rules feature completely removed, no migration needed
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
