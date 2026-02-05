# Global Agent Timeline

## Purpose
This capability defines how all agent execution steps across multiple agents are displayed in a unified chronological timeline view in the CenterPanel.

## Requirements

### Requirement: Display all agent steps in chronological order
The CenterPanel SHALL display execution steps from all agents in a single timeline ordered by timestamp.

#### Scenario: Multiple agents are executing
- **WHEN** multiple agents are running and generating steps
- **THEN** all steps SHALL be displayed in a single timeline sorted by timestamp ascending

#### Scenario: Steps from different agents interleave
- **WHEN** agent A and agent B generate steps at overlapping times
- **THEN** the timeline SHALL show steps from both agents interleaved in chronological order

### Requirement: Extract steps from all traces
The system SHALL extract execution steps from all agent traces in the traces Map.

#### Scenario: Traces Map contains multiple agents
- **WHEN** the traces Map contains multiple AgentTrace objects
- **THEN** the system SHALL extract steps from all traces and combine them

#### Scenario: New steps are added to traces
- **WHEN** new steps are added to any trace via WebSocket
- **THEN** the global timeline SHALL update to include the new steps

### Requirement: Display agent context for each step
Each step in the global timeline SHALL display which agent generated it.

#### Scenario: Step is displayed in timeline
- **WHEN** a step is rendered in the global timeline
- **THEN** the step SHALL show the agent name and ID that generated it

### Requirement: Real-time updates
The global timeline SHALL update in real-time as new steps arrive via WebSocket.

#### Scenario: New step arrives via WebSocket
- **WHEN** an agent_trace_step message is received
- **THEN** the global timeline SHALL immediately display the new step in chronological position

### Requirement: Replace old message-based display
The CenterPanel SHALL use trace data instead of the legacy currentCase.messages data.

#### Scenario: CenterPanel renders agent collaboration tab
- **WHEN** the "Agent协同" tab is active in CenterPanel
- **THEN** the panel SHALL display the global agent timeline from traces, not currentCase.messages
