# LLM Provider Configuration

## Supported Providers

The system supports multiple LLM providers with automatic fallback:

1. **OpenAI** (GPT-4, GPT-3.5-turbo)
2. **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus)
3. **Azure OpenAI** (GPT-4, GPT-3.5-turbo)

## Configuration

Set environment variables in `.env`:

```bash
# Primary provider
LLM_PRIMARY_PROVIDER=anthropic
LLM_PRIMARY_MODEL=claude-3-5-sonnet-20241022

# Fallback provider
LLM_FALLBACK_PROVIDER=openai
LLM_FALLBACK_MODEL=gpt-4

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

## Provider-Specific Settings

### OpenAI
```bash
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...  # Optional
```

### Anthropic
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### Azure OpenAI
```bash
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4  # Deployment name in Azure
```

## Fallback Chain

The system automatically retries with fallback providers on failure:

1. Try primary provider (3 retries with exponential backoff)
2. If all retries fail, try fallback provider
3. If fallback fails, return error

## Token Usage Tracking

Token usage is automatically tracked for cost estimation:

```python
from app.core.llm_factory import llm_factory

llm = llm_factory.create_with_fallback()
# Token usage logged automatically
```

## Cost Estimation

Pricing per 1M tokens (as of 2024):

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | GPT-4 | $30 | $60 |
| OpenAI | GPT-3.5-turbo | $0.50 | $1.50 |
| Anthropic | Claude 3.5 Sonnet | $3 | $15 |
| Anthropic | Claude 3 Opus | $15 | $75 |

## Best Practices

1. Use Anthropic Claude 3.5 Sonnet for primary (best cost/performance)
2. Configure OpenAI GPT-4 as fallback for reliability
3. Monitor token usage in logs
4. Set appropriate timeout values (default: 300s)
