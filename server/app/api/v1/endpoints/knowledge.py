from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.case import KnowledgeNode, KnowledgeEdge, HistoricalCase
from app.schemas.case import (
    KnowledgeDataResponse,
    KnowledgeGraphResponse,
    KnowledgeNodeResponse,
    KnowledgeEdgeResponse,
    HistoricalCaseResponse,
)
from app.repositories.knowledge_repository import KnowledgeRepository

router = APIRouter()
knowledge_repo = KnowledgeRepository()

DEFAULT_NODES = [
    {"id": "1", "type": "symptom", "label": "连接池耗尽", "x": 100, "y": 200},
    {"id": "2", "type": "symptom", "label": "请求超时", "x": 100, "y": 300},
    {"id": "3", "type": "rootCause", "label": "配置不当", "x": 300, "y": 150},
    {"id": "4", "type": "rootCause", "label": "连接泄漏", "x": 300, "y": 250},
    {"id": "5", "type": "rootCause", "label": "慢查询", "x": 300, "y": 350},
    {"id": "6", "type": "solution", "label": "增加连接池大小", "x": 500, "y": 100},
    {"id": "7", "type": "solution", "label": "修复泄漏代码", "x": 500, "y": 200},
    {"id": "8", "type": "solution", "label": "优化SQL索引", "x": 500, "y": 300},
    {"id": "9", "type": "code", "label": "HikariConfig.java", "x": 500, "y": 400},
]

DEFAULT_EDGES = [
    {"source": "1", "target": "3", "label": "可能导致"},
    {"source": "1", "target": "4", "label": "可能导致"},
    {"source": "2", "target": "5", "label": "可能导致"},
    {"source": "3", "target": "6", "label": "解决方案"},
    {"source": "4", "target": "7", "label": "解决方案"},
    {"source": "5", "target": "8", "label": "解决方案"},
    {"source": "6", "target": "9", "label": "涉及代码"},
]

DEFAULT_CASES = [
    {
        "id": "KB-001",
        "title": "MySQL连接池耗尽问题",
        "symptoms": ["Connection pool exhausted", "请求超时"],
        "root_cause": "连接池配置过小",
        "solution": "增加maximum-pool-size到300",
        "confidence": 95,
        "hits": 127,
        "last_used": "2024-01-05",
    },
    {
        "id": "KB-002",
        "title": "Kafka消费者Rebalance",
        "symptoms": ["Consumer group rebalance", "消息堆积"],
        "root_cause": "心跳超时配置不当",
        "solution": "调整session.timeout.ms",
        "confidence": 88,
        "hits": 89,
        "last_used": "2024-01-04",
    },
    {
        "id": "KB-003",
        "title": "Redis集群数据不一致",
        "symptoms": ["Cache miss增加", "数据过期异常"],
        "root_cause": "主从同步延迟",
        "solution": "检查网络延迟并优化",
        "confidence": 72,
        "hits": 45,
        "last_used": "2024-01-03",
    },
]


@router.get("", response_model=KnowledgeDataResponse)
def get_knowledge_data():
    nodes = knowledge_repo.get_all_nodes()
    edges = knowledge_repo.get_all_edges()
    cases = knowledge_repo.get_all_historical_cases()

    if not nodes:
        knowledge_repo.bulk_create_nodes([{
            "node_id": node["id"],
            "label": node["label"],
            "node_type": node["type"],
            "x": node["x"],
            "y": node["y"]
        } for node in DEFAULT_NODES])
        nodes = knowledge_repo.get_all_nodes()

    if not edges:
        knowledge_repo.bulk_create_edges([{
            "edge_id": f"e{i}",
            "source": edge["source"],
            "target": edge["target"],
            "label": edge["label"]
        } for i, edge in enumerate(DEFAULT_EDGES)])
        edges = knowledge_repo.get_all_edges()

    if not cases:
        knowledge_repo.bulk_create_historical_cases([{
            "case_id": case["id"],
            "title": case["title"],
            "symptoms": ",".join(case["symptoms"]),
            "root_cause": case["root_cause"],
            "solution": case["solution"],
            "confidence": case["confidence"],
            "hits": case["hits"]
        } for case in DEFAULT_CASES])
        cases = knowledge_repo.get_all_historical_cases()

    nodes_response = [
        KnowledgeNodeResponse(
            id=node.node_id,
            type=node.node_type,
            label=node.label,
            x=node.x,
            y=node.y,
        )
        for node in nodes
    ]

    edges_response = [
        KnowledgeEdgeResponse(
            source=edge.source,
            target=edge.target,
            label=edge.label,
        )
        for edge in edges
    ]

    cases_response = [
        HistoricalCaseResponse(
            id=case.case_id,
            title=case.title,
            symptoms=case.symptoms.split(","),
            root_cause=case.root_cause,
            solution=case.solution,
            confidence=case.confidence,
            hits=case.hits,
            last_used=case.last_used.strftime("%Y-%m-%d") if case.last_used else "",
        )
        for case in cases
    ]

    return KnowledgeDataResponse(
        graph=KnowledgeGraphResponse(nodes=nodes_response, edges=edges_response),
        historical_cases=cases_response,
    )


@router.get("/graph", response_model=KnowledgeGraphResponse)
def get_knowledge_graph():
    nodes = knowledge_repo.get_all_nodes()
    edges = knowledge_repo.get_all_edges()

    if not nodes:
        knowledge_repo.bulk_create_nodes([{
            "node_id": node["id"],
            "label": node["label"],
            "node_type": node["type"],
            "x": node["x"],
            "y": node["y"]
        } for node in DEFAULT_NODES])
        nodes = knowledge_repo.get_all_nodes()

    if not edges:
        knowledge_repo.bulk_create_edges([{
            "edge_id": f"e{i}",
            "source": edge["source"],
            "target": edge["target"],
            "label": edge["label"]
        } for i, edge in enumerate(DEFAULT_EDGES)])
        edges = knowledge_repo.get_all_edges()

    nodes_response = [
        KnowledgeNodeResponse(
            id=node.node_id,
            type=node.node_type,
            label=node.label,
            x=node.x,
            y=node.y,
        )
        for node in nodes
    ]

    edges_response = [
        KnowledgeEdgeResponse(
            source=edge.source,
            target=edge.target,
            label=edge.label,
        )
        for edge in edges
    ]

    return KnowledgeGraphResponse(nodes=nodes_response, edges=edges_response)


@router.get("/cases", response_model=List[HistoricalCaseResponse])
def get_historical_cases():
    cases = knowledge_repo.get_all_historical_cases()

    if not cases:
        knowledge_repo.bulk_create_historical_cases([{
            "case_id": case["id"],
            "title": case["title"],
            "symptoms": ",".join(case["symptoms"]),
            "root_cause": case["root_cause"],
            "solution": case["solution"],
            "confidence": case["confidence"],
            "hits": case["hits"]
        } for case in DEFAULT_CASES])
        cases = knowledge_repo.get_all_historical_cases()

    return [
        HistoricalCaseResponse(
            id=case.case_id,
            title=case.title,
            symptoms=case.symptoms.split(","),
            root_cause=case.root_cause,
            solution=case.solution,
            confidence=case.confidence,
            hits=case.hits,
            last_used=case.last_used.strftime("%Y-%m-%d") if case.last_used else "",
        )
        for case in cases
    ]


@router.get("/cases/{case_id}", response_model=HistoricalCaseResponse)
def get_historical_case(case_id: str):
    case = knowledge_repo.get_historical_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return HistoricalCaseResponse(
        id=case.case_id,
        title=case.title,
        symptoms=case.symptoms.split(","),
        root_cause=case.root_cause,
        solution=case.solution,
        confidence=case.confidence,
        hits=case.hits,
        last_used=case.last_used.strftime("%Y-%m-%d") if case.last_used else "",
    )
