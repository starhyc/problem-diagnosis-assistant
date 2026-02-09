from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Union

class OpenAIConfig(BaseModel):
    provider: Literal["openai"] = "openai"
    api_key: str = Field(..., min_length=1)
    base_url: Optional[str] = None
    models: List[str] = Field(default_factory=list)

class AnthropicConfig(BaseModel):
    provider: Literal["anthropic"] = "anthropic"
    api_key: str = Field(..., min_length=1)
    models: List[str] = Field(default_factory=list)

class AzureConfig(BaseModel):
    provider: Literal["azure"] = "azure"
    api_key: str = Field(..., min_length=1)
    base_url: str = Field(..., min_length=1)
    deployment: str = Field(..., min_length=1)
    models: List[str] = Field(default_factory=list)

    @validator('base_url')
    def validate_azure_url(cls, v):
        if not v.endswith('.openai.azure.com'):
            raise ValueError('Azure base_url must end with .openai.azure.com')
        return v

class CustomConfig(BaseModel):
    provider: Literal["custom"] = "custom"
    api_key: str = Field(..., min_length=1)
    base_url: str = Field(..., min_length=1)
    models: List[str] = Field(default_factory=list)

LLMProviderConfig = Union[OpenAIConfig, AnthropicConfig, AzureConfig, CustomConfig]
