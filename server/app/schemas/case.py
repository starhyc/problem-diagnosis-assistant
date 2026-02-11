from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class DashboardStatsResponse(BaseModel):
    active_tasks: int
    success_rate: float
    avg_resolution_time: str
    total_cases: int


class CaseResponse(BaseModel):
    id: str
    symptom: str
    status: str
    lead_agent: str
    timestamp: str
    confidence: int


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    color: str
    description: str


class SystemHealthResponse(BaseModel):
    name: str
    status: str
    latency: str


class DashboardDataResponse(BaseModel):
    stats: DashboardStatsResponse
    recent_cases: List[CaseResponse]
    system_health: dict
    agents: List[AgentResponse]


class TimelineStepResponse(BaseModel):
    id: int
    step: str
    status: str
    duration: str
    agent: str
    output: str


class AgentMessageResponse(BaseModel):
    id: int
    agent: str
    timestamp: str
    content: str
    type: str


class TopologyNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    status: str


class TopologyEdgeResponse(BaseModel):
    source: str
    target: str


class HypothesisNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    probability: Optional[float] = None
    status: Optional[str] = None
    evidence: Optional[List[str]] = None


class HypothesisTreeResponse(BaseModel):
    root: HypothesisNodeResponse


class InvestigationDataResponse(BaseModel):
    agents: List[AgentResponse]
    sample_logs: str
    topology_nodes: List[TopologyNodeResponse]
    topology_edges: List[TopologyEdgeResponse]
    hypothesis_tree: HypothesisTreeResponse


class KnowledgeNodeResponse(BaseModel):
    id: str
    type: str
    label: str
    x: int
    y: int


class KnowledgeEdgeResponse(BaseModel):
    source: str
    target: str
    label: str


class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeNodeResponse]
    edges: List[KnowledgeEdgeResponse]


class HistoricalCaseResponse(BaseModel):
    id: str
    title: str
    symptoms: List[str]
    root_cause: str
    solution: str
    confidence: int
    hits: int
    last_used: str


class HistoricalCaseCreateRequest(BaseModel):
    case_id: str
    title: str
    symptoms: List[str]
    root_cause: str
    solution: str
    confidence: int = Field(ge=0, le=100)


class HistoricalCaseUpdateRequest(BaseModel):
    title: Optional[str] = None
    symptoms: Optional[List[str]] = None
    root_cause: Optional[str] = None
    solution: Optional[str] = None
    confidence: Optional[int] = Field(default=None, ge=0, le=100)


class HistoryListItemResponse(BaseModel):
    session_id: str
    snapshot_version: int
    current_phase: str
    confidence: int
    message_count: int
    event_count: int
    service: Optional[str] = None
    problem_type: Optional[str] = None
    updated_at: datetime


class HistoryEventResponse(BaseModel):
    sequence: int
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime


class HistoryDetailResponse(BaseModel):
    session_id: str
    snapshot_version: int
    snapshot_data: Dict[str, Any]
    event_count: int
    first_event_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None
    events: List[HistoryEventResponse]


class KnowledgeDataResponse(BaseModel):
    graph: KnowledgeGraphResponse
    historical_cases: List[HistoricalCaseResponse]


class RedlineResponse(BaseModel):
    id: str
    name: str
    enabled: bool
    description: str


class ToolResponse(BaseModel):
    id: str
    name: str
    connected: bool
    url: str


class MaskingRuleResponse(BaseModel):
    pattern: str
    name: str
    replacement: str


class SettingsDataResponse(BaseModel):
    redlines: List[RedlineResponse]
    tools: List[ToolResponse]
    masking_rules: List[MaskingRuleResponse]


class AutomationPolicyResponse(BaseModel):
    automation_level: str = "balanced"
    risk_thresholds: Dict[str, int] = Field(default_factory=lambda: {
        "R0": 0,
        "R1": 1,
        "R2": 2,
        "R3": 3,
    })


class AutomationPolicyUpdateRequest(BaseModel):
    automation_level: Literal["conservative", "balanced", "aggressive"]
    risk_thresholds: Optional[Dict[Literal["R0", "R1", "R2", "R3"], int]] = None


class StartDiagnosisRequest(BaseModel):
    agent_type: str = "diagnosis"
    # 兼容说明：过渡期保留对 prd_* 旧值的解析，并映射到标准模式。
    mode: Literal["auto", "direct", "plan_execute", "react", "hierarchical"] = "auto"
    problem_description: str
    description: Optional[str] = None
    files: Optional[Dict[str, List[str]]] = None
    context: Optional[Dict[str, Any]] = None

    @validator("mode", pre=True)
    def normalize_legacy_mode(cls, value: Optional[str]):
        legacy_mapping = {
            "prd_minimal": "direct",
            "prd_standard": "plan_execute",
            "prd_deep": "react",
            "prd_swarm": "hierarchical",
        }
        if isinstance(value, str):
            normalized = value.strip().lower()
            return legacy_mapping.get(normalized, normalized)
        return value


class DiagnosisActionResponse(BaseModel):
    title: str
    confidence: int
    description: str




class StartDiagnosisResponse(BaseModel):
    status: str
    session_id: str
    task_id: str
    message: str


class DiagnosisSessionControlResponse(BaseModel):
    status: str
    session_id: str
    message: str


class DiagnosisActionDecisionResponse(BaseModel):
    status: str
    session_id: str
    action_id: str
    message: str
    reason: Optional[str] = None


class StopDiagnosisRequest(BaseModel):
    session_id: str


class ActionApprovalRequest(BaseModel):
    session_id: str
    action_id: str


class ActionRejectRequest(BaseModel):
    session_id: str
    action_id: str
    reason: Optional[str] = None


# LLM Provider schemas
class LLMProviderRequest(BaseModel):
    name: str
    provider: str  # openai, anthropic, azure, custom
    api_key: str
    base_url: Optional[str] = None
    models: Optional[List[str]] = None
    is_default: bool = False


class LLMProviderResponse(BaseModel):
    id: str
    name: str
    provider: str
    api_key_masked: str
    has_api_key: bool
    base_url: Optional[str] = None
    models: List[str]
    is_default: bool
    enabled: bool


class LLMProviderUpdateRequest(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[List[str]] = None
    is_default: Optional[bool] = None
    enabled: Optional[bool] = None


class TestConnectionResponse(BaseModel):
    success: bool
    message: str


class ModelListResponse(BaseModel):
    models: List[str]
