from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.logging_config import get_logger
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
from app.tasks.diagnosis_tasks import run_diagnosis
from app.core.session_manager import session_manager
import uuid

logger = get_logger(__name__)
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
    session_id = str(uuid.uuid4())
    mode = request.mode if hasattr(request, 'mode') else "simple"

    logger.info(f"Starting diagnosis: session_id={session_id}, problem={request.problem_description}")

    try:
        # Submit Celery task
        task = run_diagnosis.delay(session_id, request.problem_description, mode)

        return {
            "session_id": session_id,
            "task_id": task.id,
            "status": "submitted",
            "message": "Diagnosis task submitted"
        }
    except Exception as e:
        logger.error(f"Failed to start diagnosis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start diagnosis: {str(e)}")


@router.post("/stop")
def stop_diagnosis(session_id: str):
    from app.services.workflow_engine import workflow_engine
    success = workflow_engine.cancel_workflow(session_id)

    if success:
        return {"status": "stopped", "session_id": session_id, "message": "Diagnosis stopped"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    from celery.result import AsyncResult
    result = AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.state,
        "result": result.result if result.ready() else None,
        "info": result.info
    }


@router.get("/action", response_model=DiagnosisActionResponse)
def get_proposed_action():
    return DiagnosisActionResponse(
        title="增加HikariCP连接池大小",
        confidence=95,
        description="基于日志分析和配置审查，建议将maximum-pool-size从100增加到300",
    )


@router.post("/action/approve")
def approve_action(session_id: str, action_id: str):
    logger.info(f"Action approved: session_id={session_id}, action_id={action_id}")
    return {"status": "approved", "session_id": session_id, "action_id": action_id}


@router.post("/action/reject")
def reject_action(session_id: str, action_id: str, reason: str = ""):
    logger.info(f"Action rejected: session_id={session_id}, action_id={action_id}, reason={reason}")
    return {"status": "rejected", "session_id": session_id, "action_id": action_id, "reason": reason}
