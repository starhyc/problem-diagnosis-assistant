"""
Migration script to split settings table into dedicated tables
Run this after updating the models
"""
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.core.database import engine, Base
from app.models.llm_provider import LLMProvider
from app.models.external_tool import ExternalTool
from app.models.database_config import DatabaseConfig
from app.models.case import Setting
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def migrate_settings_to_new_tables():
    """Migrate data from settings table to new dedicated tables"""

    # Create new tables
    logger.info("Creating new tables...")
    Base.metadata.create_all(bind=engine, tables=[
        LLMProvider.__table__,
        ExternalTool.__table__,
        DatabaseConfig.__table__
    ])
    logger.info("New tables created successfully")

    session = Session(bind=engine)

    try:
        # Get all settings
        settings = session.query(Setting).all()
        logger.info(f"Found {len(settings)} settings to migrate")

        llm_count = 0
        tool_count = 0
        db_count = 0

        for setting in settings:
            config = json.loads(setting.config) if setting.config else {}

            # Migrate LLM providers
            if setting.setting_type == "llm_provider":
                try:
                    # Validate config has required fields
                    if not config.get("provider") or not config.get("api_key"):
                        logger.warning(f"Skipping invalid LLM provider: {setting.name}")
                        continue

                    llm_provider = LLMProvider(
                        name=setting.name,
                        provider=config.get("provider"),
                        api_key=config.get("api_key"),
                        base_url=config.get("base_url"),
                        models=json.dumps(config.get("models", [])),
                        is_default=getattr(setting, 'is_default', False),
                        enabled=setting.enabled
                    )
                    session.add(llm_provider)
                    llm_count += 1
                    logger.info(f"Migrated LLM provider: {setting.name}")
                except Exception as e:
                    logger.error(f"Failed to migrate LLM provider {setting.name}: {e}")

            # Migrate external tools
            elif setting.setting_type == "tool":
                try:
                    external_tool = ExternalTool(
                        tool_id=setting.setting_id,
                        name=setting.name,
                        tool_type=setting.setting_id,
                        url=config.get("url", ""),
                        auth_type=config.get("auth_type"),
                        auth_config=config.get("auth_config"),
                        enabled=setting.enabled
                    )
                    session.add(external_tool)
                    tool_count += 1
                    logger.info(f"Migrated external tool: {setting.name}")
                except Exception as e:
                    logger.error(f"Failed to migrate external tool {setting.name}: {e}")

            # Migrate database configs
            elif setting.setting_type == "database":
                try:
                    database_config = DatabaseConfig(
                        config_id=setting.setting_id,
                        name=setting.name,
                        db_type=config.get("type", ""),
                        host=config.get("host"),
                        port=config.get("port"),
                        database_name=config.get("database"),
                        username=config.get("user"),
                        password=config.get("password"),
                        connection_url=config.get("url"),
                        enabled=setting.enabled
                    )
                    session.add(database_config)
                    db_count += 1
                    logger.info(f"Migrated database config: {setting.name}")
                except Exception as e:
                    logger.error(f"Failed to migrate database config {setting.name}: {e}")

        # Commit the migration
        session.commit()

        # Verify migration
        verify_migration(session, llm_count, tool_count, db_count)

        logger.info(f"Migration completed successfully!")
        logger.info(f"  - LLM providers: {llm_count}")
        logger.info(f"  - External tools: {tool_count}")
        logger.info(f"  - Database configs: {db_count}")

    except Exception as e:
        session.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        session.close()


def verify_migration(session, expected_llm, expected_tools, expected_db):
    """Verify that migration completed successfully"""
    actual_llm = session.query(LLMProvider).count()
    actual_tools = session.query(ExternalTool).count()
    actual_db = session.query(DatabaseConfig).count()

    if actual_llm != expected_llm:
        raise ValueError(f"LLM provider count mismatch: expected {expected_llm}, got {actual_llm}")
    if actual_tools != expected_tools:
        raise ValueError(f"External tool count mismatch: expected {expected_tools}, got {actual_tools}")
    if actual_db != expected_db:
        raise ValueError(f"Database config count mismatch: expected {expected_db}, got {actual_db}")

    logger.info("Migration verification passed")


def add_indexes():
    """Add indexes to new tables"""
    logger.info("Adding indexes...")

    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_llm_providers_default ON llm_providers(is_default) WHERE is_default = TRUE"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_llm_providers_enabled ON llm_providers(enabled)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_external_tools_enabled ON external_tools(enabled)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_external_tools_type ON external_tools(tool_type)"))
        conn.commit()

    logger.info("Indexes added successfully")


if __name__ == "__main__":
    print("Starting settings table migration...")
    print("This will create new tables and migrate data from the settings table.")
    print()

    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("Migration cancelled")
        exit(0)

    try:
        migrate_settings_to_new_tables()
        add_indexes()
        print("\nMigration completed successfully!")
        print("\nNext steps:")
        print("1. Verify the migrated data")
        print("2. Update application code to use new tables")
        print("3. After validation, drop the old settings table")
    except Exception as e:
        print(f"\nMigration failed: {e}")
        print("Database has been rolled back to previous state")
        exit(1)
