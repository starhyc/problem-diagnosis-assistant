from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}

    ip: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "postgresql://aiops:aiops_password@localhost:5432/aiops"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    app_name: str = "AIOps 智能诊断平台"
    app_version: str = "1.0.0"
    debug: bool = True
    cors_origins: str = "http://localhost:5175,http://localhost:3000"
    log_level: str = "INFO"
    log_file: str = "logs/aiops.log"

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 3600

    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_timeout: int = 1800

    # LLM Provider settings
    llm_primary_provider: str = "anthropic"
    llm_primary_model: str = "claude-3-5-sonnet-20241022"
    llm_fallback_provider: str = "openai"
    llm_fallback_model: str = "gpt-4-turbo"

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: Optional[str] = None

    # Encryption
    encryption_key: Optional[str] = None

    # Feature flags
    use_real_agents: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
