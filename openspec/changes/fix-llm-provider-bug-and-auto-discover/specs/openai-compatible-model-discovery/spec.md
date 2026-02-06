# OPENAI-COMPATIBLE MODEL DISCOVERY CAPABILITY

## Purpose

Enable automatic model discovery from OpenAI-compatible providers without requiring manual user action.

## ADDED Requirements

### Requirement: Auto-trigger model discovery on field changes

The system SHALL automatically fetch available models when API credentials are provided, using debounced execution to prevent excessive API calls.

#### Scenario: OpenAI provider auto-discovery
- **WHEN** admin enters API key and provider type is OpenAI
- **THEN** system automatically triggers model discovery after 800ms of inactivity

#### Scenario: Custom endpoint auto-discovery
- **WHEN** admin enters API key and base URL for custom provider
- **THEN** system automatically triggers model discovery after 800ms of inactivity

#### Scenario: Azure vector-backed auto-discovery
- **WHEN** admin enters API key and base URL for Azure OpenAI
- **THEN** system automatically triggers model discovery after 800ms of inactivity

#### Scenario: Anthropic no auto-discovery
- **WHEN** admin enters API key for Anthropic provider
- **THEN** system does NOT auto-trigger discovery (uses predefined models)

#### Scenario: Insufficient credentials for auto-discovery
- **WHEN** admin enters API key without base URL for custom or Azure
- **THEN** system does NOT trigger discovery (requires both credentials)

### Requirement: Display discovered models in dropdown

The system SHALL display discovered models in a selectable dropdown when auto-discovery succeeds.

#### Scenario: Successful OpenAI discovery
- **WHEN** auto-discovery fetches OpenAI models
- **THEN** system displays dropdown with available models (e.g., gpt-4o, gpt-4o-mini, o1-preview)

#### Scenario: Successful custom endpoint discovery
- **WHEN** auto-discovery fetches from OpenAI-compatible endpoint
- **THEN** system displays dropdown with returned model names

#### Scenario: Click model to add
- **WHEN** admin clicks a model in the dropdown
- **THEN** system adds model to current model list and closes dropdown

#### Scenario: Search/filter available models
- **WHEN** system has large number of discovered models
- **THEN** admin can filter dropdown by typing partial model name

### Requirement: Manual model entry fallback

The system SHALL always allow manual model entry regardless of discovery success or failure.

#### Scenario: Manual add after discovery
- **WHEN** admin has discovered models in dropdown
- **THEN** system still displays manual entry input with "Add" button

#### Scenario: Manual add after discovery failure
- **WHEN** auto-discovery fails for any reason
- **THEN** system displays manual entry field with note prompting manual entry

#### Scenario: Add custom named model
- **WHEN** admin enters custom model name in manual input and clicks Add
- **THEN** system adds model to current model list (does not validate with provider)

### Requirement: Discovery error handling

The system SHALL handle discovery failures gracefully with user-actionable feedback.

#### Scenario: API authentication failure
- **WHEN** auto-discovery fails due to invalid credentials
- **THEN** system shows error toast and enables manual model entry

#### Scenario: Network timeout
- **WHEN** auto-discovery times out after 10 seconds
- **THEN** system shows timeout error with retry option

#### Scenario: Invalid response format
- **WHEN** discovery API returns unexpected model format
- **THEN** system shows validation error and enables manual entry

### Requirement: Discovery progress indication

The system SHALL indicate ongoing discovery operation to user.

#### Scenario: Auto-discovery in progress
- **WHEN** auto-discovery is triggered and pending
- **THEN** system shows progress indicator in model list section

#### Scenario: Discovery complete
- **WHEN** auto-discovery completes successfully
- **THEN** system shows full model list in dropdown (summary count optional)

#### Scenario: Discovery aborted
- **WHEN** user starts typing in model input while discovery is pending
- **THEN** system cancels pending discovery to prevent conflict

### Requirement: Model selection state management

The system SHALL correctly manage selected model state during and after discovery.

#### Scenario: Add model to existing list
- **WHEN** admin discovers models and selects from list
- **THEN** system appends selected model to current model list (preserves existing models)

#### Scenario: Prevent duplicate models
- **WHEN** admin attempts to add model that already exists in list
- **THEN** system shows indicator that model is already added (or silently skips)

#### Scenario: Remove discovered model
- **WHEN** admin removes previously added discovered model
- **THEN** system removes model from current list without affecting dropdown options

#### Scenario: Persist model list
- **WHEN** admin completes form submission
- **THEN** system saves all models (discovered and manually added) with provider config
