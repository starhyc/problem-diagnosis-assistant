## ADDED Requirements

### Requirement: Configure PostgreSQL connection
The system SHALL allow administrators to configure PostgreSQL database connection settings with encrypted credentials.

#### Scenario: Update PostgreSQL configuration
- **WHEN** admin submits PostgreSQL host, port, database, user, and password
- **THEN** system encrypts password and stores configuration

#### Scenario: Test PostgreSQL connection
- **WHEN** admin tests PostgreSQL configuration
- **THEN** system attempts connection and returns success or error

#### Scenario: Invalid PostgreSQL credentials
- **WHEN** admin tests with invalid credentials
- **THEN** system returns authentication error

#### Scenario: PostgreSQL host unreachable
- **WHEN** PostgreSQL host is unreachable
- **THEN** system returns connection timeout error after 10 seconds

### Requirement: Configure Redis connection
The system SHALL allow administrators to configure Redis connection settings.

#### Scenario: Update Redis configuration
- **WHEN** admin submits Redis URL and TTL settings
- **THEN** system stores configuration

#### Scenario: Update Redis with password
- **WHEN** admin submits Redis URL with password
- **THEN** system encrypts password and stores configuration

#### Scenario: Test Redis connection
- **WHEN** admin tests Redis configuration
- **THEN** system attempts connection and returns success or error

#### Scenario: Redis connection fails
- **WHEN** Redis is unreachable
- **THEN** system returns connection error

### Requirement: Database configuration validation
The system SHALL validate database configurations before saving.

#### Scenario: Missing required fields
- **WHEN** admin submits PostgreSQL config without host
- **THEN** system returns validation error

#### Scenario: Invalid port number
- **WHEN** admin submits invalid port number
- **THEN** system returns validation error

#### Scenario: Invalid Redis URL format
- **WHEN** admin submits malformed Redis URL
- **THEN** system returns validation error

### Requirement: Non-admin access restriction
The system SHALL restrict database configuration access to administrators only.

#### Scenario: Non-admin attempts to view config
- **WHEN** non-admin user attempts to view database configuration
- **THEN** system returns 403 Forbidden error

#### Scenario: Non-admin attempts to update config
- **WHEN** non-admin user attempts to update database configuration
- **THEN** system returns 403 Forbidden error
