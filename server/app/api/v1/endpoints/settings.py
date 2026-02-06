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
)
from app.repositories.setting_repository import SettingRepository
from app.middleware.permissions import admin_required
from app.schemas.user import UserResponse

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
            is_default=getattr(provider, 'is_default', False),
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

    # Unset existing default if this is being set as default
    if data.is_default:
        setting_repo.set_default_provider(None)  # Unset all defaults first

    # Create provider
    setting_id = data.name.lower().replace(" ", "-")
    config = {
        "provider": data.provider,
        "api_key": data.api_key,
        "base_url": data.base_url,
        "models": data.models or [],
    }

    setting_repo.create(**{
        "setting_type": "llm_provider",
        "setting_id": setting_id,
        "name": data.name,
        "enabled": True,
        "is_default": data.is_default,
        "config": json.dumps(config)
    })

    # Set as default if requested
    if data.is_default:
        setting_repo.set_default_provider(setting_id)

    created = setting_repo.get_by_type_and_id("llm_provider", setting_id)
    config = json.loads(created.config)

    return LLMProviderResponse(
        id=created.setting_id,
        name=created.name,
        provider=config["provider"],
        api_key=config["api_key"],
        base_url=config.get("base_url"),
        models=config.get("models", []),
        is_default=getattr(created, 'is_default', False),
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

    # Handle default update
    if data.is_default is not None and data.is_default:
        setting_repo.set_default_provider(provider_id)

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
        is_default=getattr(updated, 'is_default', False),
        enabled=updated.enabled
    )


@router.delete("/llm-providers/{provider_id}")
def delete_llm_provider(provider_id: str, user: UserResponse = Depends(admin_required)):
    """Delete an LLM provider configuration"""
    provider = setting_repo.get_by_type_and_id("llm_provider", provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if getattr(provider, 'is_default', False):
        raise HTTPException(status_code=400, detail="Cannot delete default provider. Set another provider as default first.")

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


@router.post("/llm-providers/discover-models", response_model=ModelListResponse)
def discover_models_with_config(data: dict, user: UserResponse = Depends(admin_required)):
    """Discover models using temporary configuration (for new providers)"""
    provider_type = data.get("provider")
    api_key = data.get("api_key")
    base_url = data.get("base_url")

    if not provider_type or not api_key:
        raise HTTPException(status_code=400, detail="provider and api_key are required")

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
            models = [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
            return ModelListResponse(models=models)
        elif provider_type == "azure":
            return ModelListResponse(models=[])
        else:
            return ModelListResponse(models=[])
    except Exception as e:
        logger.error(f"Model discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")
