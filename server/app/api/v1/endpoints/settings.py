from fastapi import APIRouter, Depends, HTTPException
from typing import List
import json
from app.core.logging_config import get_logger
from app.models.case import Setting
from app.schemas.case import (
    ToolResponse,
    LLMProviderRequest,
    LLMProviderResponse,
    LLMProviderUpdateRequest,
    TestConnectionResponse,
    ModelListResponse,
    DatabaseConfigRequest,
    DatabaseConfigResponse,
)
from app.repositories.setting_repository import SettingRepository
from app.middleware.permissions import admin_required
from app.schemas.case import UserResponse

logger = get_logger(__name__)
router = APIRouter()
setting_repo = SettingRepository()

DEFAULT_TOOLS = [
    {"id": "elk", "name": "ELK Stack", "connected": True, "url": "https://elk.internal:9200"},
    {"id": "gitlab", "name": "GitLab", "connected": True, "url": "https://gitlab.internal"},
    {"id": "k8s", "name": "Kubernetes", "connected": True, "url": "https://k8s.internal:6443"},
    {"id": "neo4j", "name": "Neo4j", "connected": True, "url": "bolt://neo4j.internal:7687"},
]


@router.get("/tools", response_model=List[ToolResponse])
def get_tools():
    """Get external tool configurations"""
    tools = setting_repo.get_by_type("tool")

    if not tools:
        setting_repo.bulk_create([{
            "setting_type": "tool",
            "setting_id": tool["id"],
            "name": tool["name"],
            "enabled": tool["connected"],
            "config": f'{{"url": "{tool["url"]}"}}'
        } for tool in DEFAULT_TOOLS])
        tools = setting_repo.get_by_type("tool")

    tools_response = []
    for tool in tools:
        config = json.loads(tool.config) if tool.config else {}
        tools_response.append(
            ToolResponse(
                id=tool.setting_id,
                name=tool.name,
                connected=tool.enabled,
                url=config.get("url", ""),
            )
        )

    return tools_response


@router.post("/tools/{tool_id}/test", response_model=TestConnectionResponse)
def test_tool_connection(tool_id: str, user: UserResponse = Depends(admin_required)):
    """Test external tool connection"""
    return TestConnectionResponse(success=True, message="Connection test not implemented")


# LLM Provider Management Endpoints

@router.get("/llm-providers", response_model=List[LLMProviderResponse])
def get_llm_providers(user: UserResponse = Depends(admin_required)):
    """Get all LLM provider configurations"""
    providers = setting_repo.get_by_type("llm_provider")

    response = []
    for provider in providers:
        config = json.loads(provider.config) if provider.config else {}
        response.append(LLMProviderResponse(
            id=provider.setting_id,
            name=provider.name,
            provider=config.get("provider", ""),
            api_key=config.get("api_key", ""),
            base_url=config.get("base_url"),
            models=config.get("models", []),
            is_primary=config.get("is_primary", False),
            is_fallback=config.get("is_fallback", False),
            enabled=provider.enabled
        ))

    return response


@router.post("/llm-providers", response_model=LLMProviderResponse)
def create_llm_provider(data: LLMProviderRequest, user: UserResponse = Depends(admin_required)):
    """Create a new LLM provider configuration"""
    # Check for duplicate name
    existing = setting_repo.get_by_type_and_id("llm_provider", data.name.lower().replace(" ", "-"))
    if existing:
        raise HTTPException(status_code=409, detail="Provider with this name already exists")

    # Validate primary/fallback constraints
    if data.is_primary and data.is_fallback:
        raise HTTPException(status_code=400, detail="Provider cannot be both primary and fallback")

    # Unset existing primary/fallback if needed
    if data.is_primary or data.is_fallback:
        providers = setting_repo.get_by_type("llm_provider")
        for provider in providers:
            config = json.loads(provider.config) if provider.config else {}
            if data.is_primary and config.get("is_primary"):
                config["is_primary"] = False
                setting_repo.update_config("llm_provider", provider.setting_id, json.dumps(config))
            if data.is_fallback and config.get("is_fallback"):
                config["is_fallback"] = False
                setting_repo.update_config("llm_provider", provider.setting_id, json.dumps(config))

    # Create provider
    setting_id = data.name.lower().replace(" ", "-")
    config = {
        "provider": data.provider,
        "api_key": data.api_key,
        "base_url": data.base_url,
        "models": data.models or [],
        "is_primary": data.is_primary,
        "is_fallback": data.is_fallback
    }

    setting_repo.create({
        "setting_type": "llm_provider",
        "setting_id": setting_id,
        "name": data.name,
        "enabled": True,
        "config": json.dumps(config)
    })

    created = setting_repo.get_by_type_and_id("llm_provider", setting_id)
    config = json.loads(created.config)

    return LLMProviderResponse(
        id=created.setting_id,
        name=created.name,
        provider=config["provider"],
        api_key=config["api_key"],
        base_url=config.get("base_url"),
        models=config.get("models", []),
        is_primary=config.get("is_primary", False),
        is_fallback=config.get("is_fallback", False),
        enabled=created.enabled
    )


@router.put("/llm-providers/{provider_id}", response_model=LLMProviderResponse)
def update_llm_provider(provider_id: str, data: LLMProviderUpdateRequest, user: UserResponse = Depends(admin_required)):
    """Update an existing LLM provider configuration"""
    provider = setting_repo.get_by_type_and_id("llm_provider", provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    config = json.loads(provider.config)

    # Update fields
    if data.name is not None:
        provider.name = data.name
    if data.api_key is not None:
        config["api_key"] = data.api_key
    if data.base_url is not None:
        config["base_url"] = data.base_url
    if data.models is not None:
        config["models"] = data.models
    if data.enabled is not None:
        provider.enabled = data.enabled

    # Handle primary/fallback updates
    if data.is_primary is not None or data.is_fallback is not None:
        if data.is_primary and data.is_fallback:
            raise HTTPException(status_code=400, detail="Provider cannot be both primary and fallback")

        # Unset other providers
        if data.is_primary:
            providers = setting_repo.get_by_type("llm_provider")
            for p in providers:
                if p.setting_id != provider_id:
                    p_config = json.loads(p.config)
                    if p_config.get("is_primary"):
                        p_config["is_primary"] = False
                        setting_repo.update_config("llm_provider", p.setting_id, json.dumps(p_config))
            config["is_primary"] = True

        if data.is_fallback:
            providers = setting_repo.get_by_type("llm_provider")
            for p in providers:
                if p.setting_id != provider_id:
                    p_config = json.loads(p.config)
                    if p_config.get("is_fallback"):
                        p_config["is_fallback"] = False
                        setting_repo.update_config("llm_provider", p.setting_id, json.dumps(p_config))
            config["is_fallback"] = True

    # Save updates
    setting_repo.update(provider.id, name=provider.name, enabled=provider.enabled)
    setting_repo.update_config("llm_provider", provider_id, json.dumps(config))

    updated = setting_repo.get_by_type_and_id("llm_provider", provider_id)
    config = json.loads(updated.config)

    return LLMProviderResponse(
        id=updated.setting_id,
        name=updated.name,
        provider=config["provider"],
        api_key=config["api_key"],
        base_url=config.get("base_url"),
        models=config.get("models", []),
        is_primary=config.get("is_primary", False),
        is_fallback=config.get("is_fallback", False),
        enabled=updated.enabled
    )


@router.delete("/llm-providers/{provider_id}")
def delete_llm_provider(provider_id: str, user: UserResponse = Depends(admin_required)):
    """Delete an LLM provider configuration"""
    provider = setting_repo.get_by_type_and_id("llm_provider", provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    config = json.loads(provider.config)
    if config.get("is_primary"):
        raise HTTPException(status_code=400, detail="Cannot delete primary provider. Set another provider as primary first.")

    setting_repo.delete(provider.id)
    return {"status": "deleted"}


@router.post("/llm-providers/{provider_id}/test", response_model=TestConnectionResponse)
def test_llm_provider(provider_id: str, user: UserResponse = Depends(admin_required)):
    """Test LLM provider connection"""
    provider = setting_repo.get_by_type_and_id("llm_provider", provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    config = json.loads(provider.config)
    provider_type = config.get("provider")
    api_key = config.get("api_key")
    base_url = config.get("base_url")

    try:
        if provider_type == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key=api_key,
                base_url=base_url,
                timeout=10
            )
            llm.invoke("test")
        elif provider_type == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model="claude-3-haiku-20240307",
                api_key=api_key,
                timeout=10
            )
            llm.invoke("test")
        elif provider_type == "azure":
            from langchain_openai import AzureChatOpenAI
            llm = AzureChatOpenAI(
                deployment_name=config.get("deployment", "gpt-35-turbo"),
                azure_endpoint=base_url,
                api_key=api_key,
                timeout=10
            )
            llm.invoke("test")
        else:
            # Custom provider (OpenAI-compatible)
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key=api_key,
                base_url=base_url,
                timeout=10
            )
            llm.invoke("test")

        return TestConnectionResponse(success=True, message="Connection successful")
    except Exception as e:
        logger.error(f"Connection test failed for {provider_id}: {e}")
        return TestConnectionResponse(success=False, message=str(e))


@router.get("/llm-providers/{provider_id}/models", response_model=ModelListResponse)
def get_llm_provider_models(provider_id: str, user: UserResponse = Depends(admin_required)):
    """Fetch available models from LLM provider API"""
    provider = setting_repo.get_by_type_and_id("llm_provider", provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    config = json.loads(provider.config)
    provider_type = config.get("provider")
    api_key = config.get("api_key")
    base_url = config.get("base_url")

    try:
        if provider_type == "openai" or provider_type == "custom":
            import requests
            url = f"{base_url or 'https://api.openai.com/v1'}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            return ModelListResponse(models=models)
        elif provider_type == "anthropic":
            # Anthropic doesn't have a models API, return known models
            models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            return ModelListResponse(models=models)
        elif provider_type == "azure":
            # Azure models are deployment-specific, return empty for manual entry
            return ModelListResponse(models=[])
        else:
            return ModelListResponse(models=[])
    except Exception as e:
        logger.error(f"Model discovery failed for {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


# Database Configuration Endpoints

@router.get("/databases", response_model=List[DatabaseConfigResponse])
def get_databases(user: UserResponse = Depends(admin_required)):
    """Get all database configurations"""
    databases = setting_repo.get_by_type("database")

    response = []
    for db in databases:
        config = json.loads(db.config) if db.config else {}
        response.append(DatabaseConfigResponse(
            id=db.setting_id,
            type=config.get("type", ""),
            host=config.get("host"),
            port=config.get("port"),
            database=config.get("database"),
            user=config.get("user"),
            password=config.get("password"),
            url=config.get("url")
        ))

    return response


@router.put("/databases/{db_id}", response_model=DatabaseConfigResponse)
def update_database(db_id: str, data: DatabaseConfigRequest, user: UserResponse = Depends(admin_required)):
    """Update database configuration"""
    db = setting_repo.get_by_type_and_id("database", db_id)

    if not db:
        # Create if doesn't exist
        config = {
            "type": data.type,
            "host": data.host,
            "port": data.port,
            "database": data.database,
            "user": data.user,
            "password": data.password,
            "url": data.url
        }

        setting_repo.create({
            "setting_type": "database",
            "setting_id": db_id,
            "name": data.type.upper(),
            "enabled": True,
            "config": json.dumps(config)
        })

        db = setting_repo.get_by_type_and_id("database", db_id)
    else:
        # Update existing
        config = json.loads(db.config)

        if data.host is not None:
            config["host"] = data.host
        if data.port is not None:
            config["port"] = data.port
        if data.database is not None:
            config["database"] = data.database
        if data.user is not None:
            config["user"] = data.user
        if data.password is not None:
            config["password"] = data.password
        if data.url is not None:
            config["url"] = data.url

        setting_repo.update_config("database", db_id, json.dumps(config))
        db = setting_repo.get_by_type_and_id("database", db_id)

    config = json.loads(db.config)
    return DatabaseConfigResponse(
        id=db.setting_id,
        type=config.get("type", ""),
        host=config.get("host"),
        port=config.get("port"),
        database=config.get("database"),
        user=config.get("user"),
        password=config.get("password"),
        url=config.get("url")
    )


@router.post("/databases/{db_id}/test", response_model=TestConnectionResponse)
def test_database(db_id: str, user: UserResponse = Depends(admin_required)):
    """Test database connection"""
    db = setting_repo.get_by_type_and_id("database", db_id)
    if not db:
        raise HTTPException(status_code=404, detail="Database configuration not found")

    config = json.loads(db.config)
    db_type = config.get("type")

    try:
        if db_type == "postgresql":
            import psycopg2
            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port"),
                database=config.get("database"),
                user=config.get("user"),
                password=config.get("password"),
                connect_timeout=10
            )
            conn.close()
            return TestConnectionResponse(success=True, message="PostgreSQL connection successful")
        elif db_type == "redis":
            import redis
            url = config.get("url", f"redis://{config.get('host')}:{config.get('port', 6379)}")
            r = redis.from_url(url, socket_connect_timeout=10)
            r.ping()
            return TestConnectionResponse(success=True, message="Redis connection successful")
        else:
            raise HTTPException(status_code=400, detail="Unknown database type")
    except Exception as e:
        logger.error(f"Database connection test failed for {db_id}: {e}")
        return TestConnectionResponse(success=False, message=str(e))
