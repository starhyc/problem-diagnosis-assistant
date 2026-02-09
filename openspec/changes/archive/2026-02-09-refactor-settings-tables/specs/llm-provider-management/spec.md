## MODIFIED Requirements

### Requirement: Delete LLM provider
The system SHALL allow administrators to delete provider configurations with automatic default promotion.

#### Scenario: Delete unused provider
- **WHEN** admin deletes provider that is not default
- **THEN** system removes provider record

#### Scenario: Delete default provider with auto-promotion
- **WHEN** admin deletes default provider and other enabled providers exist
- **THEN** system removes provider and automatically promotes first enabled provider as new default

#### Scenario: Delete last provider
- **WHEN** admin deletes the only remaining provider
- **THEN** system removes provider and system has no default

#### Scenario: Auto-promotion logging
- **WHEN** system auto-promotes a provider to default
- **THEN** system logs the promotion with old and new default provider names

### Requirement: Discover available models
The system SHALL fetch available models from provider API using GET method.

#### Scenario: Fetch OpenAI models
- **WHEN** admin requests model list for OpenAI provider
- **THEN** system calls GET /v1/models endpoint and returns model list

#### Scenario: Fetch Anthropic models
- **WHEN** admin requests model list for Anthropic provider
- **THEN** system returns predefined Anthropic model list

#### Scenario: API fetch fails
- **WHEN** model discovery API call fails
- **THEN** system returns error and allows manual model entry

#### Scenario: Manual model entry
- **WHEN** admin manually adds model name
- **THEN** system adds model to provider's model list

#### Scenario: Frontend model discovery
- **WHEN** frontend calls fetchModels API
- **THEN** frontend uses GET method not POST method
