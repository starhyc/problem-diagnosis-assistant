## ADDED Requirements

### Requirement: Reload LLM providers without restart
The system SHALL reload LLM provider configurations from database on each provider creation without requiring service restart.

#### Scenario: Configuration change takes effect immediately
- **WHEN** admin updates LLM provider configuration
- **THEN** next LLM creation uses updated configuration

#### Scenario: New provider available immediately
- **WHEN** admin adds new LLM provider
- **THEN** provider is available for selection without restart

#### Scenario: Deleted provider unavailable immediately
- **WHEN** admin deletes LLM provider
- **THEN** provider is no longer available for selection

#### Scenario: Primary provider change takes effect
- **WHEN** admin changes primary provider
- **THEN** next diagnosis uses new primary provider

#### Scenario: Fallback provider change takes effect
- **WHEN** admin changes fallback provider
- **THEN** next fallback attempt uses new fallback provider

### Requirement: Reload database configuration without restart
The system SHALL apply database configuration changes without requiring service restart.

#### Scenario: PostgreSQL connection updated
- **WHEN** admin updates PostgreSQL configuration
- **THEN** next database operation uses new connection settings

#### Scenario: Redis connection updated
- **WHEN** admin updates Redis configuration
- **THEN** next Redis operation uses new connection settings

### Requirement: Configuration caching
The system SHALL cache configuration reads to minimize database queries while ensuring freshness.

#### Scenario: Cache configuration per request
- **WHEN** multiple LLM calls occur in single request
- **THEN** system loads configuration once and reuses within request

#### Scenario: Fresh configuration on new request
- **WHEN** new request starts after configuration change
- **THEN** system loads fresh configuration from database

### Requirement: Hot-reload error handling
The system SHALL handle configuration reload failures gracefully without crashing service.

#### Scenario: Database unavailable during reload
- **WHEN** database is unavailable during configuration reload
- **THEN** system logs error and uses last known good configuration

#### Scenario: Invalid configuration detected
- **WHEN** reloaded configuration fails validation
- **THEN** system logs error and uses last known good configuration

#### Scenario: Decryption fails during reload
- **WHEN** configuration decryption fails during reload
- **THEN** system logs error and returns configuration error to caller

### Requirement: No in-flight request disruption
The system SHALL not disrupt in-flight requests when configuration changes.

#### Scenario: Diagnosis continues with original config
- **WHEN** configuration changes during active diagnosis
- **THEN** active diagnosis continues with configuration it started with

#### Scenario: New diagnosis uses new config
- **WHEN** new diagnosis starts after configuration change
- **THEN** new diagnosis uses updated configuration
