from typing import Optional, List
import json
from sqlalchemy.orm import Session
from app.models.case import Setting
from app.repositories.base import BaseRepository
from app.core.database import with_session
from app.core.encryption import encryption_service


class SettingRepository(BaseRepository[Setting]):
    def __init__(self):
        super().__init__(Setting)

    def _encrypt_sensitive_fields(self, config: dict, setting_type: str) -> dict:
        """Encrypt sensitive fields in config based on setting type"""
        config_copy = config.copy()

        if setting_type == "llm_provider":
            if "api_key" in config_copy and config_copy["api_key"]:
                config_copy["api_key"] = encryption_service.encrypt(config_copy["api_key"])
        elif setting_type == "database":
            if "password" in config_copy and config_copy["password"]:
                config_copy["password"] = encryption_service.encrypt(config_copy["password"])

        return config_copy

    def _decrypt_sensitive_fields(self, config: dict, setting_type: str) -> dict:
        """Decrypt sensitive fields in config based on setting type"""
        config_copy = config.copy()

        if setting_type == "llm_provider":
            if "api_key" in config_copy and config_copy["api_key"]:
                config_copy["api_key"] = encryption_service.decrypt(config_copy["api_key"])
        elif setting_type == "database":
            if "password" in config_copy and config_copy["password"]:
                config_copy["password"] = encryption_service.decrypt(config_copy["password"])

        return config_copy

    @with_session
    def get_by_type_and_id(self, session: Session, setting_type: str, setting_id: str) -> Optional[Setting]:
        setting = session.query(Setting).filter(
            Setting.setting_type == setting_type,
            Setting.setting_id == setting_id
        ).first()
        if setting:
            session.expunge(setting)
            # Decrypt config if present
            if setting.config:
                config = json.loads(setting.config)
                setting.config = json.dumps(self._decrypt_sensitive_fields(config, setting_type))
        return setting

    @with_session
    def get_by_type(self, session: Session, setting_type: str) -> List[Setting]:
        settings = session.query(Setting).filter(Setting.setting_type == setting_type).all()
        for setting in settings:
            session.expunge(setting)
            # Decrypt config if present
            if setting.config:
                config = json.loads(setting.config)
                setting.config = json.dumps(self._decrypt_sensitive_fields(config, setting_type))
        return settings

    @with_session
    def get_enabled_settings(self, session: Session, setting_type: str) -> List[Setting]:
        settings = session.query(Setting).filter(
            Setting.setting_type == setting_type,
            Setting.enabled == True
        ).all()
        for setting in settings:
            session.expunge(setting)
            # Decrypt config if present
            if setting.config:
                config = json.loads(setting.config)
                setting.config = json.dumps(self._decrypt_sensitive_fields(config, setting_type))
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
            # Encrypt sensitive fields before storing
            config_dict = json.loads(config)
            encrypted_config = self._encrypt_sensitive_fields(config_dict, setting_type)
            setting.config = json.dumps(encrypted_config)
            session.flush()
            session.expunge(setting)
        return setting

    @with_session
    def get_all_types(self, session: Session) -> List[str]:
        types = session.query(Setting.setting_type).distinct().all()
        return [t[0] for t in types]

    @with_session
    def get_default_provider(self, session: Session) -> Optional[Setting]:
        """Get the default LLM provider"""
        setting = session.query(Setting).filter(
            Setting.setting_type == "llm_provider",
            Setting.is_default == True
        ).first()
        if setting:
            session.expunge(setting)
            if setting.config:
                config = json.loads(setting.config)
                setting.config = json.dumps(self._decrypt_sensitive_fields(config, "llm_provider"))
        return setting

    @with_session
    def set_default_provider(self, session: Session, setting_id: str) -> Optional[Setting]:
        """Set a provider as default, unsetting any previous default"""
        # Unset current default
        session.query(Setting).filter(
            Setting.setting_type == "llm_provider",
            Setting.is_default == True
        ).update({"is_default": False})

        # Set new default
        setting = session.query(Setting).filter(
            Setting.setting_type == "llm_provider",
            Setting.setting_id == setting_id
        ).first()
        if setting:
            setting.is_default = True
            session.flush()
            session.expunge(setting)
        return setting
