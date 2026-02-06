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
