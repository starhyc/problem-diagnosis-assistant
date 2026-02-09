from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base


class ExternalTool(Base):
    __tablename__ = "external_tools"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    tool_type = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)
    auth_type = Column(String(50))
    auth_config = Column(Text)
    enabled = Column(Boolean, default=True)
    last_test_at = Column(DateTime)
    last_test_status = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
