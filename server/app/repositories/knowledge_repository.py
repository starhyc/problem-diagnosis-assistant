from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.case import KnowledgeNode, KnowledgeEdge, HistoricalCase
from app.repositories.base import BaseRepository
from app.core.database import with_session


class KnowledgeNodeRepository(BaseRepository[KnowledgeNode]):
    def __init__(self):
        super().__init__(KnowledgeNode)

    @with_session
    def get_by_node_id(self, session: Session, node_id: str) -> Optional[KnowledgeNode]:
        node = session.query(KnowledgeNode).filter(KnowledgeNode.node_id == node_id).first()
        if node:
            session.expunge(node)
        return node

    @with_session
    def get_nodes_by_type(self, session: Session, node_type: str) -> List[KnowledgeNode]:
        nodes = session.query(KnowledgeNode).filter(KnowledgeNode.node_type == node_type).all()
        for node in nodes:
            session.expunge(node)
        return nodes

    @with_session
    def get_all_nodes(self, session: Session) -> List[KnowledgeNode]:
        nodes = session.query(KnowledgeNode).all()
        for node in nodes:
            session.expunge(node)
        return nodes


class KnowledgeEdgeRepository(BaseRepository[KnowledgeEdge]):
    def __init__(self):
        super().__init__(KnowledgeEdge)

    @with_session
    def get_by_edge_id(self, session: Session, edge_id: str) -> Optional[KnowledgeEdge]:
        edge = session.query(KnowledgeEdge).filter(KnowledgeEdge.edge_id == edge_id).first()
        if edge:
            session.expunge(edge)
        return edge

    @with_session
    def get_edges_by_source(self, session: Session, source_id: str) -> List[KnowledgeEdge]:
        edges = session.query(KnowledgeEdge).filter(KnowledgeEdge.source_id == source_id).all()
        for edge in edges:
            session.expunge(edge)
        return edges

    @with_session
    def get_edges_by_target(self, session: Session, target_id: str) -> List[KnowledgeEdge]:
        edges = session.query(KnowledgeEdge).filter(KnowledgeEdge.target_id == target_id).all()
        for edge in edges:
            session.expunge(edge)
        return edges

    @with_session
    def get_all_edges(self, session: Session) -> List[KnowledgeEdge]:
        edges = session.query(KnowledgeEdge).all()
        for edge in edges:
            session.expunge(edge)
        return edges


class HistoricalCaseRepository(BaseRepository[HistoricalCase]):
    def __init__(self):
        super().__init__(HistoricalCase)

    @with_session
    def get_by_case_id(self, session: Session, case_id: str) -> Optional[HistoricalCase]:
        case = session.query(HistoricalCase).filter(HistoricalCase.case_id == case_id).first()
        if case:
            session.expunge(case)
        return case

    @with_session
    def search_by_symptoms(self, session: Session, symptoms: str, skip: int = 0, limit: int = 10) -> List[HistoricalCase]:
        cases = session.query(HistoricalCase).filter(
            HistoricalCase.symptoms.contains(symptoms)
        ).offset(skip).limit(limit).all()
        for case in cases:
            session.expunge(case)
        return cases

    @with_session
    def get_recent_cases(self, session: Session, skip: int = 0, limit: int = 10) -> List[HistoricalCase]:
        cases = session.query(HistoricalCase).order_by(
            HistoricalCase.last_used.desc()
        ).offset(skip).limit(limit).all()
        for case in cases:
            session.expunge(case)
        return cases

    @with_session
    def increment_hits(self, session: Session, case_id: str) -> Optional[HistoricalCase]:
        case = session.query(HistoricalCase).filter(HistoricalCase.case_id == case_id).first()
        if case:
            case.hits += 1
            session.flush()
            session.expunge(case)
        return case

    @with_session
    def get_top_cases(self, session: Session, limit: int = 10) -> List[HistoricalCase]:
        cases = session.query(HistoricalCase).order_by(
            HistoricalCase.hits.desc()
        ).limit(limit).all()
        for case in cases:
            session.expunge(case)
        return cases


class KnowledgeRepository:
    def __init__(self):
        self.nodes = KnowledgeNodeRepository()
        self.edges = KnowledgeEdgeRepository()
        self.cases = HistoricalCaseRepository()

    def get_all_nodes(self) -> List[KnowledgeNode]:
        return self.nodes.get_all_nodes()

    def get_all_edges(self) -> List[KnowledgeEdge]:
        return self.edges.get_all_edges()

    def get_all_historical_cases(self) -> List[HistoricalCase]:
        return self.cases.get_all()

    def get_historical_case_by_id(self, case_id: str) -> Optional[HistoricalCase]:
        return self.cases.get_by_case_id(case_id)

    def bulk_create_nodes(self, nodes_data: List[dict]) -> List[KnowledgeNode]:
        return self.nodes.bulk_create(nodes_data)

    def bulk_create_edges(self, edges_data: List[dict]) -> List[KnowledgeEdge]:
        return self.edges.bulk_create(edges_data)

    def bulk_create_historical_cases(self, cases_data: List[dict]) -> List[HistoricalCase]:
        return self.cases.bulk_create(cases_data)
