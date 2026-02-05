from typing import Optional, Dict, Any, Tuple
import time
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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._validate_config()
        return cls._instance

    def _validate_config(self):
        """Validate LLM provider configuration"""
        errors = []

        # Check primary provider
        if settings.llm_primary_provider == "openai" and not settings.openai_api_key:
            errors.append("Primary provider is OpenAI but OPENAI_API_KEY is not set")
        elif settings.llm_primary_provider == "anthropic" and not settings.anthropic_api_key:
            errors.append("Primary provider is Anthropic but ANTHROPIC_API_KEY is not set")
        elif settings.llm_primary_provider == "azure" and (not settings.azure_openai_api_key or not settings.azure_openai_endpoint):
            errors.append("Primary provider is Azure but Azure credentials are not set")

        # Check fallback provider
        if settings.llm_fallback_provider == "openai" and not settings.openai_api_key:
            errors.append("Fallback provider is OpenAI but OPENAI_API_KEY is not set")
        elif settings.llm_fallback_provider == "anthropic" and not settings.anthropic_api_key:
            errors.append("Fallback provider is Anthropic but ANTHROPIC_API_KEY is not set")
        elif settings.llm_fallback_provider == "azure" and (not settings.azure_openai_api_key or not settings.azure_openai_endpoint):
            errors.append("Fallback provider is Azure but Azure credentials are not set")

        if errors:
            logger.warning(f"LLM configuration issues: {'; '.join(errors)}")

    def create_llm(self, provider: Optional[str] = None, model: Optional[str] = None, **kwargs) -> BaseChatModel:
        """Create LLM instance based on provider"""
        provider = provider or settings.llm_primary_provider
        model = model or (settings.llm_primary_model if provider == settings.llm_primary_provider else settings.llm_fallback_model)

        # Add token tracking callback
        callbacks = kwargs.get('callbacks', [])
        callbacks.append(TokenUsageCallback(provider, model))
        kwargs['callbacks'] = callbacks

        try:
            if provider == "openai":
                return self._create_openai(model, **kwargs)
            elif provider == "anthropic":
                return self._create_anthropic(model, **kwargs)
            elif provider == "azure":
                return self._create_azure(model, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            logger.error(f"Failed to create LLM for provider {provider}: {e}")
            raise

    def _create_openai(self, model: str, **kwargs) -> ChatOpenAI:
        """Create OpenAI LLM instance"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        return ChatOpenAI(
            model=model,
            api_key=settings.openai_api_key,
            temperature=kwargs.get("temperature", 0),
            **kwargs
        )

    def _create_anthropic(self, model: str, **kwargs) -> ChatAnthropic:
        """Create Anthropic LLM instance"""
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")

        return ChatAnthropic(
            model=model,
            api_key=settings.anthropic_api_key,
            temperature=kwargs.get("temperature", 0),
            **kwargs
        )

    def _create_azure(self, model: str, **kwargs) -> AzureChatOpenAI:
        """Create Azure OpenAI LLM instance"""
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            raise ValueError("Azure OpenAI credentials not configured")

        return AzureChatOpenAI(
            deployment_name=settings.azure_openai_deployment or model,
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            temperature=kwargs.get("temperature", 0),
            **kwargs
        )

    def create_with_fallback(self, max_retries: int = 3, **kwargs) -> BaseChatModel:
        """Create LLM with fallback chain and retry logic"""
        providers = [
            (settings.llm_primary_provider, settings.llm_primary_model),
            (settings.llm_fallback_provider, settings.llm_fallback_model)
        ]

        for provider, model in providers:
            for attempt in range(max_retries):
                try:
                    llm = self.create_llm(provider, model, **kwargs)
                    logger.info(f"Successfully created LLM: {provider}/{model}")
                    return llm
                except Exception as e:
                    wait_time = 2 ** attempt
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {provider}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)

        raise RuntimeError("All LLM providers failed after retries")

llm_factory = LLMFactory()
