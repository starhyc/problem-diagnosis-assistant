"""
Migration utilities for moving environment variable configurations to database
"""
import json
from app.core.config import settings
from app.core.logging_config import get_logger
from app.repositories.setting_repository import SettingRepository

logger = get_logger(__name__)


def migrate_env_to_db():
    """Migrate LLM provider configurations from environment variables to database"""
    setting_repo = SettingRepository()

    # Check if migration already done
    existing_providers = setting_repo.get_by_type("llm_provider")
    if existing_providers:
        logger.info("LLM providers already exist in database, skipping migration")
        return

    logger.info("Starting migration of environment variables to database...")
    migrated = []

    # Migrate OpenAI
    if settings.openai_api_key:
        config = {
            "provider": "openai",
            "api_key": settings.openai_api_key,
            "base_url": None,
            "models": [settings.llm_primary_model if settings.llm_primary_provider == "openai" else settings.llm_fallback_model],
            "is_default": settings.llm_primary_provider == "openai",
        }

        setting_repo.create({
            "setting_type": "llm_provider",
            "setting_id": "openai-migrated",
            "name": "OpenAI (migrated from env)",
            "enabled": True,
            "config": json.dumps(config)
        })
        migrated.append("OpenAI")
        logger.info("Migrated OpenAI provider from environment variables")

    # Migrate Anthropic
    if settings.anthropic_api_key:
        config = {
            "provider": "anthropic",
            "api_key": settings.anthropic_api_key,
            "base_url": None,
            "models": [settings.llm_primary_model if settings.llm_primary_provider == "anthropic" else settings.llm_fallback_model],
            "is_default": settings.llm_primary_provider == "anthropic",
        }

        setting_repo.create({
            "setting_type": "llm_provider",
            "setting_id": "anthropic-migrated",
            "name": "Anthropic (migrated from env)",
            "enabled": True,
            "config": json.dumps(config)
        })
        migrated.append("Anthropic")
        logger.info("Migrated Anthropic provider from environment variables")

    # Migrate Azure OpenAI
    if settings.azure_openai_api_key and settings.azure_openai_endpoint:
        config = {
            "provider": "azure",
            "api_key": settings.azure_openai_api_key,
            "base_url": settings.azure_openai_endpoint,
            "models": [settings.azure_openai_deployment or "gpt-35-turbo"],
            "is_default": settings.llm_primary_provider == "azure",
        }

        setting_repo.create({
            "setting_type": "llm_provider",
            "setting_id": "azure-migrated",
            "name": "Azure OpenAI (migrated from env)",
            "enabled": True,
            "config": json.dumps(config)
        })
        migrated.append("Azure OpenAI")
        logger.info("Migrated Azure OpenAI provider from environment variables")

    if migrated:
        logger.info(f"Migration complete. Migrated providers: {', '.join(migrated)}")
        logger.warning("IMPORTANT: Environment variables are now deprecated. Manage LLM providers through the Settings UI.")
    else:
        logger.warning("No LLM providers found in environment variables. Please configure providers through the Settings UI.")
