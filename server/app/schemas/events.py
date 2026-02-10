import uuid
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    # Diagnosis lifecycle
    DIAGNOSIS_STARTED = "diagnosis_started"
    DIAGNOSIS_COMPLETED = "diagnosis_completed"
    DIAGNOSIS_FAILED = "diagnosis_failed"
    DIAGNOSIS_PAUSED = "diagnosis_paused"
    DIAGNOSIS_RESUMED = "diagnosis_resumed"
    DIAGNOSIS_CANCELLED = "diagnosis_cancelled"

    # Agent events
    # Agent trace events
    AGENT_TRACE_START = "agent_trace_start"
    AGENT_TRACE_STEP = "agent_trace_step"
    AGENT_TRACE_COMPLETE = "agent_trace_complete"

    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_MESSAGE = "agent_message"

    # Workflow events
    WORKFLOW_NODE_ENTERED = "workflow_node_entered"
    WORKFLOW_NODE_COMPLETED = "workflow_node_completed"
    WORKFLOW_EDGE_TRAVERSED = "workflow_edge_traversed"

    # State events
    STATE_UPDATED = "state_updated"
    SNAPSHOT_CREATED = "snapshot_created"
    CONFIDENCE_UPDATED = "confidence_updated"
    EVIDENCE_ADDED = "evidence_added"
    HYPOTHESIS_UPDATED = "hypothesis_updated"

    # Action events
    ACTION_PROPOSED = "action_proposed"
    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    ACTION_EXECUTED = "action_executed"

    # Confirmation events
    CONFIRMATION_REQUIRED = "confirmation_required"
    CONFIRMATION_RECEIVED = "confirmation_received"
    CONFIRMATION_TIMEOUT = "confirmation_timeout"
    CONFIRMATION_REJECTED = "confirmation_rejected"
    CONFIRMATION_ESCALATED = "confirmation_escalated"

    # Task events
    TASK_SUBMITTED = "task_submitted"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRY = "task_retry"

    # Timeline events
    TIMELINE_UPDATED = "timeline_updated"

    # Connection events
    CONNECTION_ESTABLISHED = "connection_established"
    HEARTBEAT = "heartbeat"


class BaseEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    sequence: Optional[int] = None
    parent_event_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class DiagnosisEvent(BaseEvent):
    symptom: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None


class AgentEvent(BaseEvent):
    agent_type: str
    agent_name: str
    task: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowEvent(BaseEvent):
    node_name: Optional[str] = None
    edge_from: Optional[str] = None
    edge_to: Optional[str] = None
    workflow_state: Optional[Dict[str, Any]] = None


class StateEvent(BaseEvent):
    state_field: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    snapshot_version: Optional[int] = None


class ActionEvent(BaseEvent):
    action_id: str
    action_type: Optional[str] = None
    action_description: Optional[str] = None
    reason: Optional[str] = None


class ConfirmationRiskLevel(str, Enum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"


class ConfirmationResponseAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL = "cancel"
    SECOND_CONFIRM = "second_confirm"


class ConfirmationEvent(BaseEvent):
    confirmation_id: str
    action_id: str
    message: str
    risk_level: ConfirmationRiskLevel
    impact_scope: str
    rollback_plan: str
    approver_roles: List[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    timeout_strategy: str = "auto_reject"
    requires_second_confirmation: bool = False
    status: Optional[str] = None
    response_action: Optional[ConfirmationResponseAction] = None
    response_reason: Optional[str] = None


class TaskEvent(BaseEvent):
    task_id: str
    task_name: Optional[str] = None
    progress: Optional[int] = None
    phase: Optional[str] = None
    error: Optional[str] = None


class TimelineEvent(BaseEvent):
    timeline_items: List[Dict[str, Any]] = Field(default_factory=list)
