## ADDED Requirements

### Requirement: Single-page collapsible layout
The system SHALL display all settings in a single scrollable page with collapsible sections instead of tab navigation.

#### Scenario: View all settings sections
- **WHEN** admin navigates to settings page
- **THEN** system displays all setting sections (LLM providers, external tools) in a single page

#### Scenario: Expand section
- **WHEN** admin clicks on a collapsed section header
- **THEN** system expands that section to show its content

#### Scenario: Collapse section
- **WHEN** admin clicks on an expanded section header
- **THEN** system collapses that section to hide its content

#### Scenario: Multiple sections expanded
- **WHEN** multiple sections are expanded simultaneously
- **THEN** system allows all sections to remain expanded for easy comparison

### Requirement: Section state persistence
The system SHALL remember which sections are expanded or collapsed across page reloads.

#### Scenario: Reload with expanded sections
- **WHEN** admin reloads page with sections expanded
- **THEN** system restores the same expanded/collapsed state

#### Scenario: Default state on first visit
- **WHEN** admin visits settings page for the first time
- **THEN** system displays all sections expanded by default

### Requirement: Remove tab navigation
The system SHALL NOT display tab navigation for switching between settings categories.

#### Scenario: No tab buttons
- **WHEN** admin views settings page
- **THEN** system does not display tab buttons for LLM, database, or tools

#### Scenario: Direct section access
- **WHEN** admin wants to access a specific setting
- **THEN** system allows scrolling or clicking section headers without tab switching
