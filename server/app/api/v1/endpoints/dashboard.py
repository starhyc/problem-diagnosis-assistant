from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.case import Case, Agent, SystemHealth, DashboardStats
from app.schemas.case import (
    DashboardDataResponse,
    DashboardStatsResponse,
    CaseResponse,
    AgentResponse,
    SystemHealthResponse,
)
from app.repositories.case_repository import CaseRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.system_health_repository import SystemHealthRepository
from app.repositories.dashboard_stats_repository import DashboardStatsRepository

router = APIRouter()
case_repo = CaseRepository()
agent_repo = AgentRepository()
health_repo = SystemHealthRepository()
stats_repo = DashboardStatsRepository()


@router.get("", response_model=DashboardDataResponse)
def get_dashboard_data():
    stats = stats_repo.get_stats()
    cases = case_repo.get_recent_cases(limit=10)
    agents = agent_repo.get_active_agents()
    health_records = health_repo.get_all_health_records()

    stats_response = DashboardStatsResponse(
        active_tasks=stats.active_tasks,
        success_rate=stats.success_rate,
        avg_resolution_time=stats.avg_resolution_time or "",
        total_cases=stats.total_cases,
    )

    cases_response = [
        CaseResponse(
            id=case.case_id,
            symptom=case.symptom,
            status=case.status,
            lead_agent=case.lead_agent,
            timestamp=case.created_at.strftime("%Y-%m-%d %H:%M"),
            confidence=case.confidence,
        )
        for case in cases
    ]

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

    system_health = {
        record.tool_id: SystemHealthResponse(
            name=record.name,
            status=record.status,
            latency=record.latency,
        ).dict()
        for record in health_records
    }

    return DashboardDataResponse(
        stats=stats_response,
        recent_cases=cases_response,
        system_health=system_health,
        agents=agents_response,
    )


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats():
    stats = stats_repo.get_stats()
    if not stats:
        stats = stats_repo.create_or_update(
            active_tasks=12,
            success_rate=94.2,
            avg_resolution_time="18min",
            total_cases=1247,
        )

    return DashboardStatsResponse(
        active_tasks=stats.active_tasks,
        success_rate=stats.success_rate,
        avg_resolution_time=stats.avg_resolution_time or "",
        total_cases=stats.total_cases,
    )


@router.get("/dashboard/cases", response_model=List[CaseResponse])
def get_recent_cases(skip: int = 0, limit: int = 10):
    cases = case_repo.get_recent_cases(skip=skip, limit=limit)
    return [
        CaseResponse(
            id=case.case_id,
            symptom=case.symptom,
            status=case.status,
            lead_agent=case.lead_agent,
            timestamp=case.created_at.strftime("%Y-%m-%d %H:%M"),
            confidence=case.confidence,
        )
        for case in cases
    ]


@router.get("/dashboard/agents", response_model=List[AgentResponse])
def get_agents():
    agents = agent_repo.get_active_agents()
    return [
        AgentResponse(
            id=agent.agent_id,
            name=agent.name,
            role=agent.role,
            color=agent.color,
            description=agent.description,
        )
        for agent in agents
    ]


@router.get("/system-health")
def get_system_health():
    health_records = health_repo.get_all_health_records()
    if not health_records:
        default_health = [
            SystemHealth(tool_id="elk", name="ELK Stack", status="healthy", latency="12ms"),
            SystemHealth(tool_id="git", name="GitLab", status="healthy", latency="45ms"),
            SystemHealth(tool_id="k8s", name="Kubernetes", status="warning", latency="180ms"),
            SystemHealth(tool_id="neo4j", name="Neo4j", status="healthy", latency="28ms"),
            SystemHealth(tool_id="milvus", name="Milvus", status="healthy", latency="35ms"),
        ]
        health_repo.bulk_create([{
            "tool_id": h.tool_id,
            "name": h.name,
            "status": h.status,
            "latency": h.latency
        } for h in default_health])
        health_records = default_health

    return {
        record.tool_id: SystemHealthResponse(
            name=record.name,
            status=record.status,
            latency=record.latency,
        ).dict()
        for record in health_records
    }
