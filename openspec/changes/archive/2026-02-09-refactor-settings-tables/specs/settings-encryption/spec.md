## MODIFIED Requirements

### Requirement: Encryption key management
The system SHALL manage encryption key securely and fail fast in production when missing.

#### Scenario: Production startup without encryption key
- **WHEN** system starts in production and ENCRYPTION_KEY env var is not set
- **THEN** system raises configuration error and refuses to start

#### Scenario: Development startup without encryption key
- **WHEN** system starts in development and ENCRYPTION_KEY env var is not set
- **THEN** system generates temporary 32-byte Fernet key and logs loud warning with key value

#### Scenario: Use existing encryption key
- **WHEN** system starts and ENCRYPTION_KEY env var is set
- **THEN** system uses provided key for encryption/decryption

#### Scenario: Invalid encryption key
- **WHEN** encryption key is invalid format
- **THEN** system raises configuration error on startup

#### Scenario: Environment detection
- **WHEN** system checks for production mode
- **THEN** system reads ENVIRONMENT env var and treats 'production' value as production mode

## ADDED Requirements

### Requirement: Encryption key documentation
The system SHALL provide clear guidance for encryption key setup.

#### Scenario: Key generation command in error message
- **WHEN** production startup fails due to missing key
- **THEN** error message includes command to generate valid Fernet key

#### Scenario: Development warning visibility
- **WHEN** development mode generates temporary key
- **THEN** warning message is prominently displayed with borders and includes key value to copy to .env file
