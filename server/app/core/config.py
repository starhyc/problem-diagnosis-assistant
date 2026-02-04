from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}

    ip: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./aiops.db"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    app_name: str = "AIOps 智能诊断平台"
    app_version: str = "1.0.0"
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    log_level: str = "INFO"
    log_file: str = "logs/aiops.log"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
