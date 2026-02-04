from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository
from app.core.database import with_session


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    @with_session
    def get_by_username(self, session: Session, username: str) -> Optional[User]:
        user = session.query(User).filter(User.username == username).first()
        if user:
            session.expunge(user)
        return user

    @with_session
    def get_by_email(self, session: Session, email: str) -> Optional[User]:
        user = session.query(User).filter(User.email == email).first()
        if user:
            session.expunge(user)
        return user

    @with_session
    def get_active_users(self, session: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return session.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()

    @with_session
    def get_users_by_role(self, session: Session, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        return session.query(User).filter(User.role == role).offset(skip).limit(limit).all()

    @with_session
    def update_password(self, session: Session, user_id: int, hashed_password: str) -> Optional[User]:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.hashed_password = hashed_password
            session.flush()
            session.refresh(user)
        return user

    @with_session
    def deactivate_user(self, session: Session, user_id: int) -> Optional[User]:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False
            session.flush()
            session.refresh(user)
        return user

    @with_session
    def activate_user(self, session: Session, user_id: int) -> Optional[User]:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = True
            session.flush()
            session.refresh(user)
        return user

    @with_session
    def username_exists(self, session: Session, username: str) -> bool:
        return session.query(User).filter(User.username == username).first() is not None

    @with_session
    def email_exists(self, session: Session, email: str) -> bool:
        return session.query(User).filter(User.email == email).first() is not None
