from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.case import Case
from app.repositories.base import BaseRepository
from app.core.database import with_session


class CaseRepository(BaseRepository[Case]):
    def __init__(self):
        super().__init__(Case)

    @with_session
    def get_by_case_id(self, session: Session, case_id: str) -> Optional[Case]:
        case = session.query(Case).filter(Case.case_id == case_id).first()
        if case:
            session.expunge(case)
        return case

    @with_session
    def get_recent_cases(self, session: Session, skip: int = 0, limit: int = 10) -> List[Case]:
        cases = session.query(Case).order_by(desc(Case.created_at)).offset(skip).limit(limit).all()
        for case in cases:
            session.expunge(case)
        return cases

    @with_session
    def get_cases_by_status(self, session: Session, status: str, skip: int = 0, limit: int = 100) -> List[Case]:
        cases = session.query(Case).filter(Case.status == status).offset(skip).limit(limit).all()
        for case in cases:
            session.expunge(case)
        return cases

    @with_session
    def get_cases_by_lead_agent(self, session: Session, lead_agent: str, skip: int = 0, limit: int = 100) -> List[Case]:
        cases = session.query(Case).filter(Case.lead_agent == lead_agent).offset(skip).limit(limit).all()
        for case in cases:
            session.expunge(case)
        return cases

    @with_session
    def update_status(self, session: Session, case_id: str, status: str) -> Optional[Case]:
        case = session.query(Case).filter(Case.case_id == case_id).first()
        if case:
            case.status = status
            session.flush()
            session.expunge(case)
        return case

    @with_session
    def update_confidence(self, session: Session, case_id: str, confidence: int) -> Optional[Case]:
        case = session.query(Case).filter(Case.case_id == case_id).first()
        if case:
            case.confidence = confidence
            session.flush()
            session.expunge(case)
        return case

    @with_session
    def count_by_status(self, session: Session, status: str) -> int:
        return session.query(Case).filter(Case.status == status).count()
