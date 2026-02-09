## ADDED Requirements

### Requirement: Validate OpenAI provider configuration
The system SHALL validate OpenAI provider configurations using Pydantic models before saving.

#### Scenario: Valid OpenAI configuration
- **WHEN** admin submits OpenAI provider with api_key and optional base_url
- **THEN** system validates and accepts configuration

#### Scenario: Missing API key
- **WHEN** admin submits OpenAI provider without api_key
- **THEN** system returns validation error "api_key is required"

#### Scenario: Invalid base URL format
- **WHEN** admin submits OpenAI provider with malformed base_url
- **THEN** system returns validation error with URL format requirements

### Requirement: Validate Anthropic provider configuration
The system SHALL validate Anthropic provider configurations using Pydantic models.

#### Scenario: Valid Anthropic configuration
- **WHEN** admin submits Anthropic provider with api_key
- **THEN** system validates and accepts configuration

#### Scenario: Missing API key
- **WHEN** admin submits Anthropic provider without api_key
- **THEN** system returns validation error "api_key is required"

### Requirement: Validate Azure OpenAI provider configuration
The system SHALL validate Azure OpenAI provider configurations with required deployment field.

#### Scenario: Valid Azure configuration
- **WHEN** admin submits Azure provider with api_key, base_url, and deployment
- **THEN** system validates and accepts configuration

#### Scenario: Missing deployment name
- **WHEN** admin submits Azure provider without deployment field
- **THEN** system returns validation error "deployment is required for Azure"

#### Scenario: Missing base URL
- **WHEN** admin submits Azure provider without base_url
- **THEN** system returns validation error "base_url is required for Azure"

#### Scenario: Invalid Azure endpoint format
- **WHEN** admin submits Azure provider with base_url not ending in .openai.azure.com
- **THEN** system returns validation error "Azure base_url must end with .openai.azure.com"

### Requirement: Validate custom provider configuration
The system SHALL validate custom OpenAI-compatible provider configurations.

#### Scenario: Valid custom configuration
- **WHEN** admin submits custom provider with api_key and base_url
- **THEN** system validates and accepts configuration

#### Scenario: Missing base URL for custom provider
- **WHEN** admin submits custom provider without base_url
- **THEN** system returns validation error "base_url is required for custom providers"

### Requirement: Provider-specific validation
The system SHALL apply different validation rules based on provider type.

#### Scenario: Discriminated union validation
- **WHEN** system receives provider configuration
- **THEN** system selects appropriate Pydantic model based on provider field

#### Scenario: Type-specific field requirements
- **WHEN** admin submits configuration
- **THEN** system enforces only fields required for that provider type

### Requirement: Validation error messages
The system SHALL return clear, actionable validation error messages.

#### Scenario: Multiple validation errors
- **WHEN** configuration has multiple validation failures
- **THEN** system returns all validation errors in response

#### Scenario: Field-level error details
- **WHEN** validation fails for specific field
- **THEN** system returns error with field name and requirement
