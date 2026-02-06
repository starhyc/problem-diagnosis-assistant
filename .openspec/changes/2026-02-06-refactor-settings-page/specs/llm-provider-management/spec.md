## ADDED Requirements

### Requirement: Create LLM provider
The system SHALL allow administrators to create new LLM provider configurations with encrypted credentials.

#### Scenario: Create OpenAI provider
- **WHEN** admin submits OpenAI provider with API key and base URL
- **THEN** system creates provider record with encrypted API key

#### Scenario: Create Anthropic provider
- **WHEN** admin submits Anthropic provider with API key
- **THEN** system creates provider record with encrypted API key

#### Scenario: Create Azure OpenAI provider
- **WHEN** admin submits Azure provider with API key, endpoint, and deployment name
- **THEN** system creates provider record with encrypted credentials

#### Scenario: Create custom provider
- **WHEN** admin submits custom provider with OpenAI-compatible API endpoint
- **THEN** system creates provider record with custom base URL

#### Scenario: Non-admin attempts to create provider
- **WHEN** non-admin user attempts to create provider
- **THEN** system returns 403 Forbidden error

### Requirement: List LLM providers
The system SHALL return all configured LLM providers with decrypted credentials for display.

#### Scenario: List all providers
- **WHEN** admin requests provider list
- **THEN** system returns all providers with connection status and available models

#### Scenario: Empty provider list
- **WHEN** no providers are configured
- **THEN** system returns empty array

### Requirement: Update LLM provider
The system SHALL allow administrators to update existing provider configurations.

#### Scenario: Update API key
- **WHEN** admin updates provider API key
- **THEN** system encrypts and stores new API key

#### Scenario: Update base URL
- **WHEN** admin updates provider base URL
- **THEN** system stores new URL and invalidates cached models

#### Scenario: Set as primary provider
- **WHEN** admin sets provider as primary
- **THEN** system unsets previous primary and sets new primary

#### Scenario: Set as fallback provider
- **WHEN** admin sets provider as fallback
- **THEN** system unsets previous fallback and sets new fallback

#### Scenario: Enable/disable provider
- **WHEN** admin toggles provider enabled status
- **THEN** system updates enabled flag

### Requirement: Delete LLM provider
The system SHALL allow administrators to delete provider configurations.

#### Scenario: Delete unused provider
- **WHEN** admin deletes provider that is not primary or fallback
- **THEN** system removes provider record

#### Scenario: Delete primary provider
- **WHEN** admin attempts to delete primary provider
- **THEN** system returns error requiring primary reassignment first

#### Scenario: Delete fallback provider
- **WHEN** admin deletes fallback provider
- **THEN** system removes provider and clears fallback setting

### Requirement: Test provider connection
The system SHALL allow administrators to test provider connectivity and authentication.

#### Scenario: Successful connection test
- **WHEN** admin tests provider with valid credentials
- **THEN** system makes test API call and returns success status

#### Scenario: Failed connection test
- **WHEN** admin tests provider with invalid credentials
- **THEN** system returns error message with failure reason

#### Scenario: Network timeout
- **WHEN** provider endpoint is unreachable
- **THEN** system returns timeout error after 10 seconds

### Requirement: Discover available models
The system SHALL fetch available models from provider API when possible.

#### Scenario: Fetch OpenAI models
- **WHEN** admin requests model list for OpenAI provider
- **THEN** system calls /v1/models endpoint and returns model list

#### Scenario: Fetch Anthropic models
- **WHEN** admin requests model list for Anthropic provider
- **THEN** system returns predefined Anthropic model list

#### Scenario: API fetch fails
- **WHEN** model discovery API call fails
- **THEN** system returns error and allows manual model entry

#### Scenario: Manual model entry
- **WHEN** admin manually adds model name
- **THEN** system adds model to provider's model list

### Requirement: Primary and fallback selection
The system SHALL enforce single primary and single fallback provider constraints.

#### Scenario: Only one primary allowed
- **WHEN** admin sets provider as primary
- **THEN** system automatically unsets previous primary provider

#### Scenario: Only one fallback allowed
- **WHEN** admin sets provider as fallback
- **THEN** system automatically unsets previous fallback provider

#### Scenario: Same provider cannot be both
- **WHEN** admin attempts to set provider as both primary and fallback
- **THEN** system returns validation error

### Requirement: Provider configuration validation
The system SHALL validate provider configurations before saving.

#### Scenario: Missing required fields
- **WHEN** admin submits provider without API key
- **THEN** system returns validation error

#### Scenario: Invalid URL format
- **WHEN** admin submits provider with malformed base URL
- **THEN** system returns validation error

#### Scenario: Duplicate provider name
- **WHEN** admin creates provider with existing name
- **THEN** system returns conflict error
