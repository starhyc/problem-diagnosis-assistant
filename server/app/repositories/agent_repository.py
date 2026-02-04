from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.case import Agent
from app.repositories.base import BaseRepository
from app.core.database import with_session


class AgentRepository(BaseRepository[Agent]):
    def __init__(self):
        super().__init__(Agent)

    @with_session
    def get_by_agent_id(self, session: Session, agent_id: str) -> Optional[Agent]:
        agent = session.query(Agent).filter(Agent.agent_id == agent_id).first()
        if agent:
            session.expunge(agent)
        return agent

    @with_session
    def get_active_agents(self, session: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
        agents = session.query(Agent).filter(Agent.is_active == True).offset(skip).limit(limit).all()
        for agent in agents:
            session.expunge(agent)
        return agents

    @with_session
    def get_agents_by_role(self, session: Session, role: str, skip: int = 0, limit: int = 100) -> List[Agent]:
        agents = session.query(Agent).filter(Agent.role == role).offset(skip).limit(limit).all()
        for agent in agents:
            session.expunge(agent)
        return agents

    @with_session
    def deactivate_agent(self, session: Session, agent_id: str) -> Optional[Agent]:
        agent = session.query(Agent).filter(Agent.agent_id == agent_id).first()
        if agent:
            agent.is_active = False
            session.flush()
            session.expunge(agent)
        return agent

    @with_session
    def activate_agent(self, session: Session, agent_id: str) -> Optional[Agent]:
        agent = session.query(Agent).filter(Agent.agent_id == agent_id).first()
        if agent:
            agent.is_active = True
            session.flush()
            session.expunge(agent)
        return agent

    @with_session
    def count_active_agents(self, session: Session) -> int:
        return session.query(Agent).filter(Agent.is_active == True).count()
