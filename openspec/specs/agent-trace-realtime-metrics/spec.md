# Agent Trace Real-time Metrics

## Purpose
This capability defines how execution metrics (elapsed time, accumulated tokens) are calculated and displayed in real-time during agent execution, rather than only after completion.

## Requirements

### Requirement: Calculate elapsed time during execution
The ExecutionTimeline SHALL calculate and display elapsed time from agent start until current moment for running agents.

#### Scenario: Agent is running
- **WHEN** an agent has status 'running' and startTime is available
- **THEN** the system SHALL calculate elapsed time as (current time - startTime) and display it in the metrics panel

#### Scenario: Agent has completed
- **WHEN** an agent has status 'success' or 'failed' and duration is available
- **THEN** the system SHALL display the final duration value from trace.duration

#### Scenario: Elapsed time updates periodically
- **WHEN** an agent is running
- **THEN** the elapsed time SHALL update at least once per second to reflect current execution time

### Requirement: Accumulate tokens from execution steps
The ExecutionTimeline SHALL calculate and display accumulated token usage by summing tokens from all completed execution steps.

#### Scenario: Steps contain token data
- **WHEN** execution steps include tokens field with input and output counts
- **THEN** the system SHALL sum all step tokens and display accumulated totals in the metrics panel

#### Scenario: Agent has completed with final tokens
- **WHEN** an agent has completed and trace.totalTokens is available
- **THEN** the system SHALL display the final totalTokens values instead of calculated accumulation

#### Scenario: No token data available yet
- **WHEN** no steps with token data have been received
- **THEN** the system SHALL display "0" for input and output token counts

### Requirement: Real-time metric updates
The AgentHierarchyTree SHALL display updated token counts and duration as new execution steps arrive.

#### Scenario: New step with tokens arrives
- **WHEN** a new execution step with token data is added to the trace
- **THEN** the AgentHierarchyTree SHALL re-render to display updated accumulated token counts

#### Scenario: Agent status changes
- **WHEN** an agent's status changes from 'running' to 'success' or 'failed'
- **THEN** the component SHALL re-render to display final metrics
