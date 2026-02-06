# Workflow Orchestration

## Purpose
LangGraph-based workflow orchestration with dual-mode execution and state persistence.

## Requirements

### Requirement: Dual-mode workflow execution
The system SHALL support two workflow execution modes: centralized coordination for simple tasks and LangGraph DAG orchestration for complex tasks.

#### Scenario: Simple task execution
- **WHEN** a diagnosis task has a single data source and straightforward analysis
- **THEN** the system SHALL use centralized coordination mode where the Coordinator agent directly delegates to a single specialized agent

#### Scenario: Complex task execution
- **WHEN** a diagnosis task requires multiple data sources, parallel analysis, or conditional branching
- **THEN** the system SHALL use LangGraph DAG mode with a predefined workflow graph

### Requirement: LangGraph workflow definition
The system SHALL use LangGraph 0.2+ to define diagnosis workflows as state machines.

#### Scenario: Workflow state definition
- **WHEN** a LangGraph workflow is created
- **THEN** it SHALL define a DiagnosisState TypedDict containing symptom, messages, hypothesis_tree, evidence, confidence, and next_action fields

#### Scenario: Workflow node registration
- **WHEN** a workflow is initialized
- **THEN** it SHALL register nodes for each agent (coordinator, log_analysis, code_analysis, knowledge_matching, metric_analysis)

#### Scenario: Conditional edges
- **WHEN** a workflow node completes
- **THEN** the system SHALL evaluate conditional edges to determine the next node based on the current state

### Requirement: Workflow execution control
The system SHALL provide controls for pausing, resuming, and canceling workflow execution.

#### Scenario: Workflow pause
- **WHEN** a user requests to pause a running workflow
- **THEN** the system SHALL complete the current node execution and pause before the next node

#### Scenario: Workflow resume
- **WHEN** a user resumes a paused workflow
- **THEN** the system SHALL continue execution from the next pending node

#### Scenario: Workflow cancellation
- **WHEN** a user cancels a running workflow
- **THEN** the system SHALL immediately stop execution and mark the diagnosis session as cancelled

### Requirement: Workflow persistence
The system SHALL persist workflow state at each node completion for recovery.

#### Scenario: Node completion checkpoint
- **WHEN** a workflow node completes successfully
- **THEN** the system SHALL save a state snapshot to the database before proceeding to the next node

#### Scenario: Workflow recovery
- **WHEN** a workflow execution is interrupted
- **THEN** the system SHALL be able to resume from the last completed node using the persisted state
