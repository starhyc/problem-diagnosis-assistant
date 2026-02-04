from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from functools import wraps
import inspect
import datetime

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


@contextmanager
def session_scope() -> Session:
    """上下文管理器用于自动获取 Session, 避免错误"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def with_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with session_scope() as session:
            try:
                if args and hasattr(args[0], '__class__'):
                    result = f(args[0], session, *args[1:], **kwargs)
                else:
                    result = f(session, *args, **kwargs)
                session.commit()
                return result
            except:
                session.rollback()
                raise
    return wrapper

def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()