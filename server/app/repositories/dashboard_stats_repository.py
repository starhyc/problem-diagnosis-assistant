from typing import Optional
from sqlalchemy.orm import Session
from app.models.case import DashboardStats
from app.repositories.base import BaseRepository
from app.core.database import with_session


class DashboardStatsRepository(BaseRepository[DashboardStats]):
    def __init__(self):
        super().__init__(DashboardStats)

    @with_session
    def get_stats(self, session: Session) -> Optional[DashboardStats]:
        stats = session.query(DashboardStats).first()
        if stats:
            session.expunge(stats)
        return stats

    @with_session
    def update_active_tasks(self, session: Session, active_tasks: int) -> Optional[DashboardStats]:
        stats = session.query(DashboardStats).first()
        if not stats:
            stats = DashboardStats(active_tasks=active_tasks)
            session.add(stats)
        else:
            stats.active_tasks = active_tasks
        session.flush()
        session.expunge(stats)
        return stats

    @with_session
    def update_success_rate(self, session: Session, success_rate: float) -> Optional[DashboardStats]:
        stats = session.query(DashboardStats).first()
        if not stats:
            stats = DashboardStats(success_rate=success_rate)
            session.add(stats)
        else:
            stats.success_rate = success_rate
        session.flush()
        session.expunge(stats)
        return stats

    @with_session
    def update_avg_resolution_time(self, session: Session, avg_resolution_time: str) -> Optional[DashboardStats]:
        stats = session.query(DashboardStats).first()
        if not stats:
            stats = DashboardStats(avg_resolution_time=avg_resolution_time)
            session.add(stats)
        else:
            stats.avg_resolution_time = avg_resolution_time
        session.flush()
        session.expunge(stats)
        return stats

    @with_session
    def update_total_cases(self, session: Session, total_cases: int) -> Optional[DashboardStats]:
        stats = session.query(DashboardStats).first()
        if not stats:
            stats = DashboardStats(total_cases=total_cases)
            session.add(stats)
        else:
            stats.total_cases = total_cases
        session.flush()
        session.expunge(stats)
        return stats

    @with_session
    def increment_total_cases(self, session: Session) -> Optional[DashboardStats]:
        stats = session.query(DashboardStats).first()
        if not stats:
            stats = DashboardStats(total_cases=1)
            session.add(stats)
        else:
            stats.total_cases += 1
        session.flush()
        session.expunge(stats)
        return stats

    @with_session
    def create_or_update(self, session: Session, **kwargs) -> DashboardStats:
        stats = session.query(DashboardStats).first()
        if not stats:
            stats = DashboardStats(**kwargs)
            session.add(stats)
        else:
            for key, value in kwargs.items():
                setattr(stats, key, value)
        session.flush()
        session.refresh(stats)
        return stats
