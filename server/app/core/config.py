from typing import List, Optional
from urllib.parse import urlparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}

    ip: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"

    database_url: str = "postgresql://aiops:aiops_password@localhost:5432/aiops"
    secret_key: Optional[str] = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    app_name: str = "AIOps 智能诊断平台"
    app_version: str = "1.0.0"
    debug: bool = False
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
    enable_demo_trace: bool = False
    agent_tool_map: Optional[str] = None  # JSON string, e.g. {"log": ["elk_query"]}

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"development", "staging", "production", "test"}:
            raise ValueError("environment must be one of: development, staging, production, test")
        return normalized

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"postgresql", "postgresql+psycopg2", "sqlite"}:
            raise ValueError("DATABASE_URL must use postgresql/postgresql+psycopg2/sqlite scheme")
        if parsed.scheme.startswith("postgresql") and not parsed.hostname:
            raise ValueError("DATABASE_URL must include a hostname")
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"redis", "rediss"}:
            raise ValueError("REDIS_URL must use redis:// or rediss://")
        if not parsed.hostname:
            raise ValueError("REDIS_URL must include a hostname")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one allowed origin")

        for origin in origins:
            parsed = urlparse(origin)
            if parsed.scheme not in {"http", "https"}:
                raise ValueError(f"Invalid CORS origin scheme: {origin}")
            if not parsed.netloc:
                raise ValueError(f"Invalid CORS origin host: {origin}")

        return ",".join(origins)

    @model_validator(mode="after")
    def validate_security(self) -> "Settings":
        secret = (self.secret_key or "").strip()
        if self.environment == "production" and not secret:
            raise ValueError("SECRET_KEY is required in production")
        if secret and len(secret) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return self

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
