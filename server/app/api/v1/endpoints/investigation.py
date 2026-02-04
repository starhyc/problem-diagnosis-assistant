from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.case import Agent
from app.schemas.case import (
    InvestigationDataResponse,
    AgentResponse,
    TopologyNodeResponse,
    TopologyEdgeResponse,
    HypothesisTreeResponse,
    HypothesisNodeResponse,
    StartDiagnosisRequest,
    DiagnosisActionResponse,
)
from app.repositories.agent_repository import AgentRepository

router = APIRouter()
agent_repo = AgentRepository()

SAMPLE_LOGS = """2024-01-05 15:29:45.123 [http-nio-8080-exec-42] ERROR c.e.s.OrderService - Failed to process order
com.zaxxer.hikari.pool.HikariPool$PoolEntryCreator - Connection is not available, request timed out after 30000ms.
    at com.zaxxer.hikari.pool.HikariPool.createTimeoutException(HikariPool.java:696)
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:197)
    at com.example.service.OrderService.createOrder(OrderService.java:89)
    at com.example.controller.OrderController.create(OrderController.java:45)

2024-01-05 15:29:46.234 [http-nio-8080-exec-43] WARN  c.z.h.p.HikariPool - HikariPool-1 - Thread starvation detected
Active connections: 100, Idle: 0, Waiting threads: 47

2024-01-05 15:29:47.456 [http-nio-8080-exec-44] ERROR c.e.s.OrderService - Database connection timeout
java.sql.SQLTransientConnectionException: HikariPool-1 - Connection is not available
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:155)
    at com.example.repository.OrderRepository.save(OrderRepository.java:34)"""

TOPOLOGY_NODES = [
    {"id": "gateway", "label": "API Gateway", "type": "service", "status": "healthy"},
    {"id": "user-svc", "label": "User Service", "type": "service", "status": "healthy"},
    {"id": "order-svc", "label": "Order Service", "type": "service", "status": "error"},
    {"id": "payment-svc", "label": "Payment Service", "type": "service", "status": "healthy"},
    {"id": "mysql", "label": "MySQL", "type": "database", "status": "warning"},
    {"id": "redis", "label": "Redis", "type": "cache", "status": "healthy"},
    {"id": "kafka", "label": "Kafka", "type": "queue", "status": "healthy"},
]

TOPOLOGY_EDGES = [
    {"source": "gateway", "target": "user-svc"},
    {"source": "gateway", "target": "order-svc"},
    {"source": "order-svc", "target": "payment-svc"},
    {"source": "user-svc", "target": "mysql"},
    {"source": "order-svc", "target": "mysql"},
    {"source": "payment-svc", "target": "mysql"},
    {"source": "user-svc", "target": "redis"},
    {"source": "order-svc", "target": "kafka"},
]

HYPOTHESIS_TREE = {
    "root": HypothesisNodeResponse(
        id="root",
        label="MySQL连接池耗尽",
        type="symptom",
        probability=None,
        status=None,
        evidence=None,
    ).dict()
}


@router.get("", response_model=InvestigationDataResponse)
def get_investigation_data():
    agents = agent_repo.get_active_agents()

    if not agents:
        default_agents = [
            Agent(
                agent_id="coordinator",
                name="协调Agent",
                role="Coordinator",
                color="#3b82f6",
                description="统筹全局任务分发与结果综合",
            ),
            Agent(
                agent_id="log",
                name="日志分析Agent",
                role="Log Analyst",
                color="#f59e0b",
                description="专注ELK日志解析与异常检测",
            ),
            Agent(
                agent_id="code",
                name="代码分析Agent",
                role="Code Analyst",
                color="#10b981",
                description="专注AST解析与调用链追踪",
            ),
            Agent(
                agent_id="knowledge",
                name="架构审查Agent",
                role="Architecture Reviewer",
                color="#8b5cf6",
                description="专注知识图谱与架构模式匹配",
            ),
        ]
        agent_repo.bulk_create([{
            "agent_id": a.agent_id,
            "name": a.name,
            "role": a.role,
            "color": a.color,
            "description": a.description
        } for a in default_agents])
        agents = default_agents

    agents_response = [
        AgentResponse(
            id=agent.agent_id,
            name=agent.name,
            role=agent.role,
            color=agent.color,
            description=agent.description,
        )
        for agent in agents
    ]

    topology_nodes = [TopologyNodeResponse(**node) for node in TOPOLOGY_NODES]
    topology_edges = [TopologyEdgeResponse(**edge) for edge in TOPOLOGY_EDGES]
    hypothesis_tree = HypothesisTreeResponse(root=HYPOTHESIS_TREE["root"])

    return InvestigationDataResponse(
        agents=agents_response,
        sample_logs=SAMPLE_LOGS,
        topology_nodes=topology_nodes,
        topology_edges=topology_edges,
        hypothesis_tree=hypothesis_tree,
    )


@router.post("/start")
def start_diagnosis(request: StartDiagnosisRequest):
    agent_type = request.agent_type or "diagnosis"
    return {
        "case_id": f"CASE-{agent_type.upper()}-{agent_repo.count() + 1}",
        "agent_type": agent_type,
        "status": "started",
        "message": f"{agent_type} 已启动",
    }


@router.post("/stop")
def stop_diagnosis():
    return {"status": "stopped", "message": "诊断已停止"}


@router.get("/action", response_model=DiagnosisActionResponse)
def get_proposed_action():
    return DiagnosisActionResponse(
        title="增加HikariCP连接池大小",
        confidence=95,
        description="基于日志分析和配置审查，建议将maximum-pool-size从100增加到300",
    )


@router.post("/action/approve")
def approve_action():
    return {"status": "approved", "message": "操作已批准"}


@router.post("/action/reject")
def reject_action():
    return {"status": "rejected", "message": "操作已拒绝"}
