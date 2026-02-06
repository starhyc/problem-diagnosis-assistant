## MODIFIED Requirements

### Requirement: Update LLM provider
The system SHALL allow administrators to update existing provider configurations.

#### Scenario: Update API key
- **WHEN** admin updates provider API key
- **THEN** system encrypts and stores new API key

#### Scenario: Update base URL
- **WHEN** admin updates provider base URL
- **THEN** system stores new URL and invalidates cached models

#### Scenario: Set as default provider
- **WHEN** admin sets provider as default
- **THEN** system unsets previous default and sets new default

#### Scenario: Enable/disable provider
- **WHEN** admin toggles provider enabled status
- **THEN** system updates enabled flag

### Requirement: Delete LLM provider
The system SHALL allow administrators to delete provider configurations.

#### Scenario: Delete unused provider
- **WHEN** admin deletes provider that is not default
- **THEN** system removes provider record

#### Scenario: Delete default provider
- **WHEN** admin attempts to delete default provider
- **THEN** system returns error requiring default reassignment first

### Requirement: Default provider selection
The system SHALL enforce single default provider constraint.

#### Scenario: Only one default allowed
- **WHEN** admin sets provider as default
- **THEN** system automatically unsets previous default provider

#### Scenario: At least one provider must be default
- **WHEN** system has multiple enabled providers
- **THEN** system requires exactly one provider to be marked as default

## REMOVED Requirements

### Requirement: Primary and fallback selection
**Reason**: Simplified to single default provider model for better UX and reduced complexity
**Migration**: Existing primary providers will be migrated to default providers. Fallback providers will remain as enabled non-default providers.
