from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True, nullable=False)
    symptom = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    lead_agent = Column(String(50), nullable=False)
    confidence = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False, default="diagnosis")
    color = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class SystemHealth(Base):
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="healthy")
    latency = Column(String(20), nullable=False)
    url = Column(String(255), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now())


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(50), unique=True, index=True, nullable=False)
    label = Column(String(200), nullable=False)
    node_type = Column(String(50), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id = Column(Integer, primary_key=True, index=True)
    edge_id = Column(String(50), unique=True, index=True, nullable=False)
    source = Column(String(50), nullable=False)
    target = Column(String(50), nullable=False)
    label = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class HistoricalCase(Base):
    __tablename__ = "historical_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    symptoms = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    confidence = Column(Integer, nullable=False)
    hits = Column(Integer, default=0)
    last_used = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())


class DashboardStats(Base):
    __tablename__ = "dashboard_stats"

    id = Column(Integer, primary_key=True, index=True)
    active_tasks = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_resolution_time = Column(String(20), nullable=True)
    total_cases = Column(Integer, default=0)
    updated_at = Column(DateTime, onupdate=func.now())


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_type = Column(String(50), nullable=False, index=True)
    setting_id = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    config = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    config_schema = Column(Text, nullable=True)
    default_config = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
