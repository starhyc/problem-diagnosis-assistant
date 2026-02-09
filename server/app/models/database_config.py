from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base


class DatabaseConfig(Base):
    __tablename__ = "database_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    db_type = Column(String(50), nullable=False)
    host = Column(String(255))
    port = Column(Integer)
    database_name = Column(String(255))
    username = Column(String(255))
    password = Column(Text)
    connection_url = Column(Text)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
