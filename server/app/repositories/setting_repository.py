from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.case import Setting
from app.repositories.base import BaseRepository
from app.core.database import with_session


class SettingRepository(BaseRepository[Setting]):
    def __init__(self):
        super().__init__(Setting)

    @with_session
    def get_by_type_and_id(self, session: Session, setting_type: str, setting_id: str) -> Optional[Setting]:
        setting = session.query(Setting).filter(
            Setting.setting_type == setting_type,
            Setting.setting_id == setting_id
        ).first()
        if setting:
            session.expunge(setting)
        return setting

    @with_session
    def get_by_type(self, session: Session, setting_type: str) -> List[Setting]:
        settings = session.query(Setting).filter(Setting.setting_type == setting_type).all()
        for setting in settings:
            session.expunge(setting)
        return settings

    @with_session
    def get_enabled_settings(self, session: Session, setting_type: str) -> List[Setting]:
        settings = session.query(Setting).filter(
            Setting.setting_type == setting_type,
            Setting.enabled == True
        ).all()
        for setting in settings:
            session.expunge(setting)
        return settings

    @with_session
    def update_enabled(self, session: Session, setting_type: str, setting_id: str, enabled: bool) -> Optional[Setting]:
        setting = session.query(Setting).filter(
            Setting.setting_type == setting_type,
            Setting.setting_id == setting_id
        ).first()
        if setting:
            setting.enabled = enabled
            session.flush()
            session.expunge(setting)
        return setting

    @with_session
    def update_config(self, session: Session, setting_type: str, setting_id: str, config: str) -> Optional[Setting]:
        setting = session.query(Setting).filter(
            Setting.setting_type == setting_type,
            Setting.setting_id == setting_id
        ).first()
        if setting:
            setting.config = config
            session.flush()
            session.expunge(setting)
        return setting

    @with_session
    def get_all_types(self, session: Session) -> List[str]:
        types = session.query(Setting.setting_type).distinct().all()
        return [t[0] for t in types]
