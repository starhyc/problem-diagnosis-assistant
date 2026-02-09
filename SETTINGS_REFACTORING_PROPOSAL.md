# Settings Architecture Refactoring Proposal

## Problem Statement

Currently, all settings (LLM providers, external tools, database configs) are stored in a single `settings` table with a `setting_type` discriminator. This creates several issues:

1. **Schema ambiguity**: Different setting types need different fields, forcing everything into a generic JSON `config` column
2. **No type safety**: Database can't enforce constraints specific to each setting type
3. **Query inefficiency**: Always filtering by `setting_type`
4. **Maintenance complexity**: Changes to one type affect the entire table
5. **Validation difficulty**: Config validation happens in application code, not at database level

## Proposed Solution: Separate Tables

### New Database Schema

```sql
-- LLM Providers Table
CREATE TABLE llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL,  -- openai, anthropic, azure, custom
    api_key TEXT NOT NULL,  -- encrypted
    base_url VARCHAR(500),
    models TEXT NOT NULL,  -- JSON array
    is_default BOOLEAN DEFAULT FALSE,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    CONSTRAINT only_one_default CHECK (
        NOT is_default OR (
            SELECT COUNT(*) FROM llm_providers WHERE is_default = TRUE
        ) <= 1
    )
);

CREATE INDEX idx_llm_providers_default ON llm_providers(is_default) WHERE is_default = TRUE;
CREATE INDEX idx_llm_providers_enabled ON llm_providers(enabled);

-- External Tools Table
CREATE TABLE external_tools (
    id SERIAL PRIMARY KEY,
    tool_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    tool_type VARCHAR(50) NOT NULL,  -- elk, gitlab, k8s, neo4j, custom
    url VARCHAR(500) NOT NULL,
    auth_type VARCHAR(50),  -- none, basic, token, oauth
    auth_config TEXT,  -- encrypted JSON
    enabled BOOLEAN DEFAULT TRUE,
    last_test_at TIMESTAMP,
    last_test_status VARCHAR(20),  -- success, failed, unknown
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX idx_external_tools_enabled ON external_tools(enabled);
CREATE INDEX idx_external_tools_type ON external_tools(tool_type);

-- Database Configs Table (if needed)
CREATE TABLE database_configs (
    id SERIAL PRIMARY KEY,
    config_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    db_type VARCHAR(50) NOT NULL,  -- postgresql, redis, mongodb
    host VARCHAR(255),
    port INTEGER,
    database_name VARCHAR(255),
    username VARCHAR(255),
    password TEXT,  -- encrypted
    connection_url TEXT,  -- encrypted, for URL-based configs
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Migration: Drop old settings table after data migration
-- DROP TABLE settings;
```

### Migration Strategy

```python
# server/migrations/migrate_settings_to_separate_tables.py

from sqlalchemy.orm import Session
from app.models.case import Setting
from app.repositories.setting_repository import SettingRepository
import json

def migrate_settings(session: Session):
    """Migrate data from settings table to new dedicated tables"""

    setting_repo = SettingRepository()

    # Migrate LLM Providers
    llm_providers = setting_repo.get_by_type("llm_provider")
    for provider in llm_providers:
        config = json.loads(provider.config)
        session.execute("""
            INSERT INTO llm_providers (name, provider, api_key, base_url, models, is_default, enabled)
            VALUES (:name, :provider, :api_key, :base_url, :models, :is_default, :enabled)
        """, {
            "name": provider.name,
            "provider": config.get("provider"),
            "api_key": config.get("api_key"),  # Already encrypted
            "base_url": config.get("base_url"),
            "models": json.dumps(config.get("models", [])),
            "is_default": getattr(provider, 'is_default', False),
            "enabled": provider.enabled
        })

    # Migrate External Tools
    tools = setting_repo.get_by_type("tool")
    for tool in tools:
        config = json.loads(tool.config) if tool.config else {}
        session.execute("""
            INSERT INTO external_tools (tool_id, name, tool_type, url, enabled)
            VALUES (:tool_id, :name, :tool_type, :url, :enabled)
        """, {
            "tool_id": tool.setting_id,
            "name": tool.name,
            "tool_type": tool.setting_id,  # elk, gitlab, etc.
            "url": config.get("url", ""),
            "enabled": tool.enabled
        })

    session.commit()
```

## Issue Fixes

### 1. HTTP Method Mismatch

**File**: `src/lib/api.ts:348-351`

```typescript
// BEFORE (WRONG)
async fetchModels(id: string): Promise<string[]> {
  return request(`/settings/llm-providers/${id}/models`, {
    method: 'POST',  // ❌ Wrong method
  });
}

// AFTER (CORRECT)
async fetchModels(id: string): Promise<string[]> {
  const response = await request<{ models: string[] }>(
    `/settings/llm-providers/${id}/models`
  );
  return response.models;
}
```

### 2. Encryption Key Management

**File**: `server/app/core/encryption.py:19-35`

```python
# BEFORE
def _initialize(self):
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        key = Fernet.generate_key().decode()
        logger.warning("ENCRYPTION_KEY not set. Generated key...")  # ❌ Silent failure

# AFTER
def _initialize(self):
    key = os.getenv("ENCRYPTION_KEY")

    if not key:
        # In production, fail fast
        if os.getenv("ENVIRONMENT") == "production":
            raise ValueError(
                "ENCRYPTION_KEY must be set in production. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        # In development, generate but warn loudly
        key = Fernet.generate_key().decode()
        logger.warning(
            f"\n{'='*70}\n"
            f"⚠️  ENCRYPTION_KEY NOT SET - GENERATED TEMPORARY KEY\n"
            f"{'='*70}\n"
            f"Key: {key}\n"
            f"Add to .env: ENCRYPTION_KEY={key}\n"
            f"{'='*70}\n"
        )

    try:
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")
```

### 3. Default Provider Deletion Logic

**File**: `server/app/api/v1/endpoints/settings.py:183-194`

```python
# BEFORE
@router.delete("/llm-providers/{provider_id}")
def delete_llm_provider(provider_id: str, user: UserResponse = Depends(admin_required)):
    provider = setting_repo.get_by_type_and_id("llm_provider", provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if getattr(provider, 'is_default', False):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default provider. Set another provider as default first."
        )  # ❌ Forces manual intervention

    setting_repo.delete(provider.id)
    return {"status": "deleted"}

# AFTER
@router.delete("/llm-providers/{provider_id}")
def delete_llm_provider(provider_id: str, user: UserResponse = Depends(admin_required)):
    provider = setting_repo.get_by_type_and_id("llm_provider", provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    was_default = getattr(provider, 'is_default', False)

    # Delete the provider
    setting_repo.delete(provider.id)

    # If it was default, auto-promote the first enabled provider
    if was_default:
        remaining_providers = setting_repo.get_enabled_settings("llm_provider")
        if remaining_providers:
            setting_repo.set_default_provider(remaining_providers[0].setting_id)
            logger.info(f"Auto-promoted {remaining_providers[0].name} as default provider")

    return {"status": "deleted", "auto_promoted": was_default and len(remaining_providers) > 0}
```

### 4. Tool Connection Testing

**File**: `server/app/api/v1/endpoints/settings.py:60-63`

```python
# BEFORE
@router.post("/tools/{tool_id}/test", response_model=TestConnectionResponse)
def test_tool_connection(tool_id: str, user: UserResponse = Depends(admin_required)):
    return TestConnectionResponse(success=True, message="Connection test not implemented")  # ❌ Stub

# AFTER
@router.post("/tools/{tool_id}/test", response_model=TestConnectionResponse)
def test_tool_connection(tool_id: str, user: UserResponse = Depends(admin_required)):
    tool = setting_repo.get_by_type_and_id("tool", tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    config = json.loads(tool.config) if tool.config else {}
    url = config.get("url", "")

    try:
        import requests
        response = requests.get(url, timeout=5)

        # Update last test status
        setting_repo.update(tool.id, **{
            "last_test_at": datetime.now(),
            "last_test_status": "success" if response.ok else "failed"
        })

        return TestConnectionResponse(
            success=response.ok,
            message=f"Connected successfully (HTTP {response.status_code})" if response.ok
                   else f"Connection failed (HTTP {response.status_code})"
        )
    except requests.exceptions.Timeout:
        return TestConnectionResponse(success=False, message="Connection timeout")
    except requests.exceptions.ConnectionError:
        return TestConnectionResponse(success=False, message="Connection refused")
    except Exception as e:
        logger.error(f"Tool test failed for {tool_id}: {e}")
        return TestConnectionResponse(success=False, message=str(e))
```

### 5. Config Validation with Pydantic

**File**: `server/app/schemas/llm_config.py` (new file)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal

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
    base_url: str = Field(..., min_length=1)  # Required for Azure
    deployment: str = Field(..., min_length=1)  # Azure deployment name
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

# Union type for validation
LLMProviderConfig = OpenAIConfig | AnthropicConfig | AzureConfig | CustomConfig
```

**Update endpoint to use validation**:

```python
@router.post("/llm-providers", response_model=LLMProviderResponse)
def create_llm_provider(data: LLMProviderRequest, user: UserResponse = Depends(admin_required)):
    # Validate config based on provider type
    config_data = {
        "provider": data.provider,
        "api_key": data.api_key,
        "base_url": data.base_url,
        "models": data.models or [],
    }

    # Validate with Pydantic
    try:
        if data.provider == "openai":
            validated = OpenAIConfig(**config_data)
        elif data.provider == "anthropic":
            validated = AnthropicConfig(**config_data)
        elif data.provider == "azure":
            validated = AzureConfig(**config_data)
        else:
            validated = CustomConfig(**config_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Continue with creation...
```

### 6. Remove Unused Database Settings API

If database configuration should only be via environment variables (as stated in CLAUDE.md), remove these endpoints:

**File**: `src/lib/api.ts:362-377`

```typescript
// DELETE THESE (lines 362-377)
async getDatabases(): Promise<any[]> {
  return request('/settings/databases');
},

async updateDatabase(id: string, config: any): Promise<any> {
  return request(`/settings/databases/${id}`, {
    method: 'PUT',
    body: JSON.stringify(config),
  });
},

async testDatabase(id: string): Promise<any> {
  return request(`/settings/databases/${id}/test`, {
    method: 'POST',
  });
},
```

## Implementation Priority

1. **Critical (Fix Now)**:
   - HTTP method mismatch (breaks functionality)
   - Encryption key management (data loss risk)

2. **High (Next Sprint)**:
   - Database schema refactoring
   - Config validation
   - Default provider deletion logic

3. **Medium (Future)**:
   - Tool connection testing
   - Remove unused database settings API

4. **Low (Nice to Have)**:
   - Tool CRUD operations
   - Granular permissions

## Testing Checklist

- [ ] LLM provider CRUD operations work with new schema
- [ ] Encryption/decryption works correctly
- [ ] Default provider auto-promotion on deletion
- [ ] Model discovery works (GET not POST)
- [ ] Tool connection testing returns real results
- [ ] Migration script successfully moves data
- [ ] No data loss during migration
- [ ] API backward compatibility (if needed)
