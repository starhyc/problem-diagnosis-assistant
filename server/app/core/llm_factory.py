from typing import Optional, Dict, Any, Tuple
import time
import json
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.callbacks import BaseCallbackHandler
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Token pricing per 1M tokens (input, output)
TOKEN_PRICING = {
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-4": (30.0, 60.0),
    "gpt-3.5-turbo": (0.5, 1.5),
    "claude-3-5-sonnet-20241022": (3.0, 15.0),
    "claude-3-opus-20240229": (15.0, 75.0),
}

class TokenUsageCallback(BaseCallbackHandler):
    """Callback to track token usage and costs"""

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def on_llm_end(self, response, **kwargs):
        """Track token usage from LLM response"""
        if hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('token_usage', {})
            self.prompt_tokens = usage.get('prompt_tokens', 0)
            self.completion_tokens = usage.get('completion_tokens', 0)
            self.total_tokens = usage.get('total_tokens', 0)

            cost = self.estimate_cost()
            logger.info(f"LLM Usage - Provider: {self.provider}, Model: {self.model}, "
                       f"Tokens: {self.total_tokens} (prompt: {self.prompt_tokens}, "
                       f"completion: {self.completion_tokens}), Cost: ${cost:.4f}")

    def estimate_cost(self) -> float:
        """Estimate cost based on token usage"""
        pricing = TOKEN_PRICING.get(self.model, (0, 0))
        input_cost = (self.prompt_tokens / 1_000_000) * pricing[0]
        output_cost = (self.completion_tokens / 1_000_000) * pricing[1]
        return input_cost + output_cost

class LLMFactory:
    _instance: Optional['LLMFactory'] = None
    _last_config = None  # Cache for configuration

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_providers_from_db(self) -> Dict[str, Any]:
        """Load LLM provider configurations from database"""
        try:
            from app.repositories.setting_repository import SettingRepository
            setting_repo = SettingRepository()
            providers = setting_repo.get_by_type("llm_provider")

            if not providers:
                # Fallback to environment variables
                logger.warning("No LLM providers in database, falling back to environment variables")
                return self._load_from_env()

            config = {"primary": None, "fallback": None, "providers": {}}

            for provider in providers:
                if not provider.enabled:
                    continue

                provider_config = json.loads(provider.config) if provider.config else {}
                provider_id = provider.setting_id

                config["providers"][provider_id] = {
                    "provider": provider_config.get("provider"),
                    "api_key": provider_config.get("api_key"),
                    "base_url": provider_config.get("base_url"),
                    "models": provider_config.get("models", []),
                }

                # Use is_default column instead of config JSON
                if hasattr(provider, 'is_default') and provider.is_default:
                    config["primary"] = provider_id
                # All other enabled providers serve as fallback
                elif not config.get("fallback"):
                    config["fallback"] = provider_id

            if not config["primary"]:
                logger.warning("No default provider configured, falling back to environment variables")
                return self._load_from_env()

            return config
        except Exception as e:
            logger.error(f"Failed to load providers from database: {e}")
            return self._load_from_env()

    def _load_from_env(self) -> Dict[str, Any]:
        """Fallback to environment variable configuration"""
        config = {"primary": None, "fallback": None, "providers": {}}

        if settings.openai_api_key:
            config["providers"]["openai-env"] = {
                "provider": "openai",
                "api_key": settings.openai_api_key,
                "base_url": None,
                "models": [settings.llm_primary_model if settings.llm_primary_provider == "openai" else settings.llm_fallback_model],
            }
            if settings.llm_primary_provider == "openai":
                config["primary"] = "openai-env"
            elif settings.llm_fallback_provider == "openai":
                config["fallback"] = "openai-env"

        if settings.anthropic_api_key:
            config["providers"]["anthropic-env"] = {
                "provider": "anthropic",
                "api_key": settings.anthropic_api_key,
                "base_url": None,
                "models": [settings.llm_primary_model if settings.llm_primary_provider == "anthropic" else settings.llm_fallback_model],
            }
            if settings.llm_primary_provider == "anthropic":
                config["primary"] = "anthropic-env"
            elif settings.llm_fallback_provider == "anthropic":
                config["fallback"] = "anthropic-env"

        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            config["providers"]["azure-env"] = {
                "provider": "azure",
                "api_key": settings.azure_openai_api_key,
                "base_url": settings.azure_openai_endpoint,
                "models": [settings.azure_openai_deployment or "gpt-35-turbo"],
            }
            if settings.llm_primary_provider == "azure":
                config["primary"] = "azure-env"
            elif settings.llm_fallback_provider == "azure":
                config["fallback"] = "azure-env"

        return config

    def create_llm(self, provider: Optional[str] = None, model: Optional[str] = None, **kwargs) -> BaseChatModel:
        """Create LLM instance based on provider"""
        # Load fresh configuration from database
        config = self._load_providers_from_db()

        # Determine which provider to use
        if provider:
            provider_id = provider
        else:
            provider_id = config.get("primary")
            if not provider_id:
                raise ValueError("No primary provider configured")

        provider_config = config["providers"].get(provider_id)
        if not provider_config:
            raise ValueError(f"Provider {provider_id} not found")

        provider_type = provider_config["provider"]
        api_key = provider_config["api_key"]
        base_url = provider_config.get("base_url")
        models = provider_config.get("models", [])

        # Determine model
        if not model:
            model = models[0] if models else "gpt-3.5-turbo"

        # Add token tracking callback
        callbacks = kwargs.get('callbacks', [])
        callbacks.append(TokenUsageCallback(provider_type, model))
        kwargs['callbacks'] = callbacks

        try:
            if provider_type == "openai":
                return self._create_openai(model, api_key, base_url, **kwargs)
            elif provider_type == "anthropic":
                return self._create_anthropic(model, api_key, **kwargs)
            elif provider_type == "azure":
                return self._create_azure(model, api_key, base_url, **kwargs)
            elif provider_type == "custom":
                return self._create_openai(model, api_key, base_url, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {provider_type}")
        except Exception as e:
            logger.error(f"Failed to create LLM for provider {provider_id}: {e}")
            raise

    def _create_openai(self, model: str, api_key: str, base_url: Optional[str] = None, **kwargs) -> ChatOpenAI:
        """Create OpenAI LLM instance"""
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=kwargs.get("temperature", 0),
            **kwargs
        )

    def _create_anthropic(self, model: str, api_key: str, **kwargs) -> ChatAnthropic:
        """Create Anthropic LLM instance"""
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=kwargs.get("temperature", 0),
            **kwargs
        )

    def _create_azure(self, model: str, api_key: str, endpoint: str, **kwargs) -> AzureChatOpenAI:
        """Create Azure OpenAI LLM instance"""
        return AzureChatOpenAI(
            deployment_name=model,
            azure_endpoint=endpoint,
            api_key=api_key,
            temperature=kwargs.get("temperature", 0),
            **kwargs
        )

    def create_with_fallback(self, max_retries: int = 3, **kwargs) -> BaseChatModel:
        """Create LLM with fallback chain and retry logic"""
        config = self._load_providers_from_db()

        primary_id = config.get("primary")
        fallback_id = config.get("fallback")

        providers_to_try = []
        if primary_id:
            providers_to_try.append(primary_id)
        if fallback_id:
            providers_to_try.append(fallback_id)

        if not providers_to_try:
            raise RuntimeError("No providers configured")

        for provider_id in providers_to_try:
            for attempt in range(max_retries):
                try:
                    llm = self.create_llm(provider_id, **kwargs)
                    logger.info(f"Successfully created LLM: {provider_id}")
                    return llm
                except Exception as e:
                    wait_time = 2 ** attempt
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {provider_id}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)

        raise RuntimeError("All LLM providers failed after retries")

llm_factory = LLMFactory()
