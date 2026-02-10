from typing import Optional, List, Union
import json
from sqlalchemy.orm import Session
from app.models.case import Setting
from app.models.llm_provider import LLMProvider
from app.models.external_tool import ExternalTool
from app.models.database_config import DatabaseConfig
from app.repositories.base import BaseRepository
from app.core.database import with_session
from app.core.encryption import encryption_service


class SettingRepository(BaseRepository[Setting]):
    def __init__(self):
        super().__init__(Setting)

    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key"""
        return encryption_service.encrypt(api_key) if api_key else ""

    def _decrypt_api_key(self, api_key: str) -> str:
        """Decrypt API key"""
        return encryption_service.decrypt(api_key) if api_key else ""

    def _mask_api_key(self, api_key: str) -> str:
        """Mask API key for safe response output."""
        if not api_key:
            return ""
        if len(api_key) <= 4:
            return "***"
        if api_key.startswith("sk-"):
            return f"sk-***{api_key[-4:]}"
        return f"***{api_key[-4:]}"

    def _build_provider_config(self, provider: LLMProvider, include_api_key: bool = False) -> dict:
        decrypted_api_key = self._decrypt_api_key(provider.api_key)
        config = {
            "provider": provider.provider,
            "api_key_masked": self._mask_api_key(decrypted_api_key),
            "has_api_key": bool(decrypted_api_key),
            "base_url": provider.base_url,
            "models": json.loads(provider.models) if provider.models else [],
        }
        if include_api_key:
            config["api_key"] = decrypted_api_key
        return config

    @with_session
    def get_by_type_and_id(self, session: Session, setting_type: str, setting_id: str, include_api_key: bool = False) -> Optional[Setting]:
        """Get setting by type and ID - routes to appropriate table"""
        if setting_type == "llm_provider":
            provider = session.query(LLMProvider).filter(LLMProvider.name == setting_id).first()
            if provider:
                session.expunge(provider)
                # Convert to Setting-like object for backward compatibility
                setting = Setting()
                setting.setting_type = "llm_provider"
                setting.setting_id = setting_id
                setting.name = provider.name
                setting.enabled = provider.enabled
                setting.is_default = provider.is_default
                setting.config = json.dumps(self._build_provider_config(provider, include_api_key=include_api_key))
                return setting
        elif setting_type == "tool":
            tool = session.query(ExternalTool).filter(ExternalTool.tool_id == setting_id).first()
            if tool:
                session.expunge(tool)
                setting = Setting()
                setting.setting_type = "tool"
                setting.setting_id = tool.tool_id
                setting.name = tool.name
                setting.enabled = tool.enabled
                setting.config = json.dumps({"url": tool.url})
                return setting
        return None

    @with_session
    def get_by_type(self, session: Session, setting_type: str, include_api_key: bool = False) -> List[Setting]:
        """Get all settings of a type - routes to appropriate table"""
        settings = []

        if setting_type == "llm_provider":
            providers = session.query(LLMProvider).all()
            for provider in providers:
                session.expunge(provider)
                setting = Setting()
                setting.id = provider.id
                setting.setting_type = "llm_provider"
                setting.setting_id = provider.name.lower().replace(" ", "-")
                setting.name = provider.name
                setting.enabled = provider.enabled
                setting.is_default = provider.is_default
                setting.config = json.dumps(self._build_provider_config(provider, include_api_key=include_api_key))
                settings.append(setting)
        elif setting_type == "tool":
            tools = session.query(ExternalTool).all()
            for tool in tools:
                session.expunge(tool)
                setting = Setting()
                setting.id = tool.id
                setting.setting_type = "tool"
                setting.setting_id = tool.tool_id
                setting.name = tool.name
                setting.enabled = tool.enabled
                setting.config = json.dumps({"url": tool.url})
                settings.append(setting)

        return settings

    @with_session
    def get_enabled_settings(self, session: Session, setting_type: str, include_api_key: bool = False) -> List[Setting]:
        """Get enabled settings of a type"""
        settings = []

        if setting_type == "llm_provider":
            providers = session.query(LLMProvider).filter(LLMProvider.enabled == True).all()
            for provider in providers:
                session.expunge(provider)
                setting = Setting()
                setting.id = provider.id
                setting.setting_type = "llm_provider"
                setting.setting_id = provider.name.lower().replace(" ", "-")
                setting.name = provider.name
                setting.enabled = provider.enabled
                setting.is_default = provider.is_default
                setting.config = json.dumps(self._build_provider_config(provider, include_api_key=include_api_key))
                settings.append(setting)

        return settings

    @with_session
    def get_default_provider(self, session: Session, include_api_key: bool = False) -> Optional[Setting]:
        """Get the default LLM provider"""
        provider = session.query(LLMProvider).filter(LLMProvider.is_default == True).first()
        if provider:
            session.expunge(provider)
            setting = Setting()
            setting.setting_type = "llm_provider"
            setting.setting_id = provider.name.lower().replace(" ", "-")
            setting.name = provider.name
            setting.enabled = provider.enabled
            setting.is_default = provider.is_default
            setting.config = json.dumps(self._build_provider_config(provider, include_api_key=include_api_key))
            return setting
        return None

    @with_session
    def set_default_provider(self, session: Session, setting_id: Optional[str]) -> Optional[Setting]:
        """Set a provider as default, unsetting any previous default"""
        # Unset all defaults
        session.query(LLMProvider).filter(LLMProvider.is_default == True).update({"is_default": False})

        if setting_id:
            # Set new default
            provider = session.query(LLMProvider).filter(
                LLMProvider.name == setting_id
            ).first()
            if provider:
                provider.is_default = True
                session.flush()
                session.expunge(provider)

                setting = Setting()
                setting.setting_type = "llm_provider"
                setting.setting_id = setting_id
                setting.name = provider.name
                setting.enabled = provider.enabled
                setting.is_default = provider.is_default
                return setting
        return None

    @with_session
    def create(self, session: Session, **kwargs) -> Setting:
        """Create a new setting - routes to appropriate table"""
        setting_type = kwargs.get("setting_type")

        if setting_type == "llm_provider":
            config = json.loads(kwargs.get("config", "{}"))
            provider = LLMProvider(
                name=kwargs.get("name"),
                provider=config.get("provider"),
                api_key=self._encrypt_api_key(config.get("api_key", "")),
                base_url=config.get("base_url"),
                models=json.dumps(config.get("models", [])),
                is_default=kwargs.get("is_default", False),
                enabled=kwargs.get("enabled", True)
            )
            session.add(provider)
            session.flush()
            session.expunge(provider)
        elif setting_type == "tool":
            config = json.loads(kwargs.get("config", "{}"))
            tool = ExternalTool(
                tool_id=kwargs.get("setting_id"),
                name=kwargs.get("name"),
                tool_type=kwargs.get("setting_id"),
                url=config.get("url", ""),
                enabled=kwargs.get("enabled", True)
            )
            session.add(tool)
            session.flush()
            session.expunge(tool)

        return Setting()

    @with_session
    def update(self, session: Session, id: int, **kwargs):
        """Update a setting - currently only used for name and enabled"""
        # This method is called by the API but we handle updates differently now
        pass

    @with_session
    def update_config(self, session: Session, setting_type: str, setting_id: str, config: str):
        """Update config for a setting"""
        if setting_type == "llm_provider":
            provider = session.query(LLMProvider).filter(LLMProvider.name == setting_id).first()
            if provider:
                config_dict = json.loads(config)
                provider.provider = config_dict.get("provider", provider.provider)
                if "api_key" in config_dict:
                    provider.api_key = self._encrypt_api_key(config_dict.get("api_key", ""))
                provider.base_url = config_dict.get("base_url", provider.base_url)
                provider.models = json.dumps(config_dict.get("models", json.loads(provider.models) if provider.models else []))
                session.flush()

    @with_session
    def delete(self, session: Session, id: int):
        """Delete a setting by ID"""
        # Try to find in LLM providers
        provider = session.query(LLMProvider).filter(LLMProvider.id == id).first()
        if provider:
            session.delete(provider)
            session.flush()
            return

        # Try to find in external tools
        tool = session.query(ExternalTool).filter(ExternalTool.id == id).first()
        if tool:
            session.delete(tool)
            session.flush()
            return

    @with_session
    def bulk_create(self, session: Session, settings: List[dict]):
        """Bulk create settings"""
        for setting_data in settings:
            self.create(**setting_data)
