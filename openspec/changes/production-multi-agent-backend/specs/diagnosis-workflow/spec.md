## ADDED Requirements

### Requirement: Dynamic workflow generation
The system SHALL generate diagnosis workflows dynamically based on symptom analysis rather than using hardcoded flows.

#### Scenario: Symptom-based workflow selection
- **WHEN** a diagnosis request is received with a symptom description
- **THEN** the Coordinator agent SHALL analyze the symptom and select the appropriate workflow mode (centralized or LangGraph DAG)

#### Scenario: Adaptive workflow branching
- **WHEN** a workflow node produces results
- **THEN** the system SHALL evaluate the results and dynamically determine the next steps based on confidence levels and evidence quality

### Requirement: Multi-phase diagnosis workflow
The system SHALL execute diagnosis in phases: symptom analysis, evidence collection, hypothesis generation, verification, and conclusion.

#### Scenario: Symptom analysis phase
- **WHEN** a diagnosis workflow starts
- **THEN** the Coordinator agent SHALL analyze the symptom and generate initial hypotheses

#### Scenario: Evidence collection phase
- **WHEN** hypotheses are generated
- **THEN** the system SHALL dispatch Log, Code, and Metric agents in parallel to collect evidence

#### Scenario: Hypothesis verification phase
- **WHEN** evidence is collected
- **THEN** the Coordinator agent SHALL evaluate evidence against hypotheses and update confidence scores

#### Scenario: Conclusion phase
- **WHEN** confidence exceeds 80% or all evidence sources are exhausted
- **THEN** the system SHALL generate a final diagnosis with root cause and recommended actions

### Requirement: Workflow state transitions
The system SHALL track workflow state transitions and publish updates to clients.

#### Scenario: State transition events
- **WHEN** the workflow transitions between phases
- **THEN** the system SHALL publish a `workflow_state_changed` event with the new state

#### Scenario: Progress tracking
- **WHEN** a workflow node completes
- **THEN** the system SHALL update the progress percentage based on completed nodes vs total nodes

### Requirement: Workflow timeout handling
The system SHALL enforce timeouts at both workflow and node levels.

#### Scenario: Node timeout
- **WHEN** a workflow node execution exceeds its timeout (default 5 minutes)
- **THEN** the system SHALL cancel the node and proceed with partial results

#### Scenario: Workflow timeout
- **WHEN** the entire workflow exceeds the configured timeout (default 30 minutes)
- **THEN** the system SHALL terminate the workflow and return partial diagnosis results
