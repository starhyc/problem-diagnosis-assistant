## ADDED Requirements

### Requirement: Encrypt sensitive data
The system SHALL encrypt API keys and passwords before storing in database using Fernet symmetric encryption.

#### Scenario: Encrypt API key
- **WHEN** system stores LLM provider API key
- **THEN** system encrypts key using Fernet and stores as base64 string

#### Scenario: Encrypt database password
- **WHEN** system stores database password
- **THEN** system encrypts password using Fernet and stores as base64 string

#### Scenario: Encrypt Redis password
- **WHEN** system stores Redis password in URL
- **THEN** system extracts and encrypts password separately

### Requirement: Decrypt sensitive data
The system SHALL decrypt encrypted data when reading from database.

#### Scenario: Decrypt API key for display
- **WHEN** system retrieves LLM provider configuration
- **THEN** system decrypts API key for display in UI

#### Scenario: Decrypt credentials for connection
- **WHEN** system uses database credentials
- **THEN** system decrypts password before establishing connection

#### Scenario: Decrypt for LLM factory
- **WHEN** LLM factory creates provider instance
- **THEN** system decrypts API key for authentication

### Requirement: Encryption key management
The system SHALL manage encryption key securely and generate if missing.

#### Scenario: Generate encryption key on first startup
- **WHEN** system starts and ENCRYPTION_KEY env var is not set
- **THEN** system generates 32-byte Fernet key and logs warning to set it

#### Scenario: Use existing encryption key
- **WHEN** system starts and ENCRYPTION_KEY env var is set
- **THEN** system uses provided key for encryption/decryption

#### Scenario: Invalid encryption key
- **WHEN** encryption key is invalid format
- **THEN** system raises configuration error on startup

### Requirement: Encryption error handling
The system SHALL handle encryption/decryption failures gracefully.

#### Scenario: Decryption fails with wrong key
- **WHEN** system attempts to decrypt with different key than used for encryption
- **THEN** system raises decryption error and logs warning

#### Scenario: Corrupted encrypted data
- **WHEN** encrypted data is corrupted or tampered
- **THEN** system raises integrity error due to Fernet authentication

#### Scenario: Plaintext data migration
- **WHEN** system encounters plaintext data during migration
- **THEN** system encrypts plaintext and updates record

### Requirement: Selective field encryption
The system SHALL only encrypt sensitive fields, not entire configuration.

#### Scenario: Encrypt only API key in LLM config
- **WHEN** system stores LLM provider configuration
- **THEN** system encrypts api_key field but leaves provider, base_url, models in plaintext

#### Scenario: Encrypt only password in database config
- **WHEN** system stores database configuration
- **THEN** system encrypts password field but leaves host, port, database, user in plaintext

#### Scenario: Non-sensitive fields remain plaintext
- **WHEN** system stores configuration with non-sensitive data
- **THEN** system stores non-sensitive fields as plaintext JSON for queryability
