from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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


class StartDiagnosisRequest(BaseModel):
    agent_type: str = "diagnosis"
    problem_description: str
    description: Optional[str] = None
    files: Optional[Dict[str, List[str]]] = None
    context: Optional[Dict[str, Any]] = None


class DiagnosisActionResponse(BaseModel):
    title: str
    confidence: int
    description: str
