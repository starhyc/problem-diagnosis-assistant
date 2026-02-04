from typing import TypeVar, Type, Generic, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from app.core.database import with_session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    @with_session
    def get_by_id(self, session: Session, id: int) -> Optional[ModelType]:
        obj = session.query(self.model).filter(self.model.id == id).first()
        if obj:
            session.expunge(obj)
        return obj

    @with_session
    def get_all(self, session: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        objs = session.query(self.model).offset(skip).limit(limit).all()
        for obj in objs:
            session.expunge(obj)
        return objs

    @with_session
    def create(self, session: Session, **kwargs) -> ModelType:
        db_obj = self.model(**kwargs)
        session.add(db_obj)
        session.flush()
        session.expunge(db_obj)
        return db_obj

    @with_session
    def update(self, session: Session, id: int, **kwargs) -> Optional[ModelType]:
        db_obj = session.query(self.model).filter(self.model.id == id).first()
        if db_obj:
            for key, value in kwargs.items():
                setattr(db_obj, key, value)
            session.flush()
            session.expunge(db_obj)
        return db_obj

    @with_session
    def delete(self, session: Session, id: int) -> bool:
        db_obj = session.query(self.model).filter(self.model.id == id).first()
        if db_obj:
            session.delete(db_obj)
            return True
        return False

    @with_session
    def count(self, session: Session) -> int:
        return session.query(self.model).count()

    @with_session
    def exists(self, session: Session, **kwargs) -> bool:
        return session.query(self.model).filter_by(**kwargs).first() is not None

    @with_session
    def get_by(self, session: Session, **kwargs) -> Optional[ModelType]:
        obj = session.query(self.model).filter_by(**kwargs).first()
        if obj:
            session.expunge(obj)
        return obj

    @with_session
    def get_all_by(self, session: Session, **kwargs) -> List[ModelType]:
        objs = session.query(self.model).filter_by(**kwargs).all()
        for obj in objs:
            session.expunge(obj)
        return objs

    @with_session
    def bulk_create(self, session: Session, objects: List[dict]) -> List[ModelType]:
        db_objs = [self.model(**obj) for obj in objects]
        session.add_all(db_objs)
        session.flush()
        for obj in db_objs:
            session.expunge(obj)
        return db_objs

    @with_session
    def bulk_update(self, session: Session, ids: List[int], **kwargs) -> int:
        result = session.query(self.model).filter(self.model.id.in_(ids)).update(kwargs, synchronize_session=False)
        session.flush()
        return result

    @with_session
    def bulk_delete(self, session: Session, ids: List[int]) -> int:
        result = session.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
        session.flush()
        return result
