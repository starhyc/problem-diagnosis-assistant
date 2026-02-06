## ADDED Requirements

### Requirement: Remove database configuration UI
The system SHALL NOT provide UI for configuring database connections.

#### Scenario: No database settings section
- **WHEN** admin views settings page
- **THEN** system does not display database configuration section

#### Scenario: Database config via environment only
- **WHEN** system needs database connection parameters
- **THEN** system reads configuration from environment variables only

### Requirement: Display LLM providers section
The system SHALL display LLM provider configuration in a collapsible section.

#### Scenario: View LLM providers
- **WHEN** admin expands LLM providers section
- **THEN** system displays list of configured providers with add/edit/delete actions

#### Scenario: Default badge display
- **WHEN** admin views provider list
- **THEN** system displays "默认" badge on the default provider

### Requirement: Display external tools section
The system SHALL display external tool connection status in a collapsible section.

#### Scenario: View external tools
- **WHEN** admin expands external tools section
- **THEN** system displays list of tools with connection status and test action

#### Scenario: Read-only tool display
- **WHEN** admin views external tools
- **THEN** system displays tools as read-only with no edit or delete actions

### Requirement: Fix form label styling
The system SHALL display form labels with proper text color for visibility.

#### Scenario: Modal form labels visible
- **WHEN** admin opens LLM provider form modal
- **THEN** system displays all form labels with text-text-main color class for visibility on dark background
