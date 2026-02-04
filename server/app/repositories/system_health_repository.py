from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.case import SystemHealth
from app.repositories.base import BaseRepository
from app.core.database import with_session


class SystemHealthRepository(BaseRepository[SystemHealth]):
    def __init__(self):
        super().__init__(SystemHealth)

    @with_session
    def get_by_tool_id(self, session: Session, tool_id: str) -> Optional[SystemHealth]:
        record = session.query(SystemHealth).filter(SystemHealth.tool_id == tool_id).first()
        if record:
            session.expunge(record)
        return record

    @with_session
    def get_all_health_records(self, session: Session) -> List[SystemHealth]:
        records = session.query(SystemHealth).all()
        for record in records:
            session.expunge(record)
        return records

    @with_session
    def update_status(self, session: Session, tool_id: str, status: str) -> Optional[SystemHealth]:
        record = session.query(SystemHealth).filter(SystemHealth.tool_id == tool_id).first()
        if record:
            record.status = status
            session.flush()
            session.expunge(record)
        return record

    @with_session
    def update_latency(self, session: Session, tool_id: str, latency: str) -> Optional[SystemHealth]:
        record = session.query(SystemHealth).filter(SystemHealth.tool_id == tool_id).first()
        if record:
            record.latency = latency
            session.flush()
            session.expunge(record)
        return record

    @with_session
    def get_by_status(self, session: Session, status: str) -> List[SystemHealth]:
        records = session.query(SystemHealth).filter(SystemHealth.status == status).all()
        for record in records:
            session.expunge(record)
        return records

    @with_session
    def count_by_status(self, session: Session, status: str) -> int:
        return session.query(SystemHealth).filter(SystemHealth.status == status).count()
