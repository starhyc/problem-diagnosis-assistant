## 1. Database Schema

- [x] 1.1 Create Alembic migration file for new tables
- [x] 1.2 Define llm_providers table schema with columns: id, name, provider, api_key, base_url, models, is_default, enabled, created_at, updated_at
- [x] 1.3 Define external_tools table schema with columns: id, tool_id, name, tool_type, url, auth_type, auth_config, enabled, last_test_at, last_test_status, created_at, updated_at
- [x] 1.4 Define database_configs table schema with columns: id, config_id, name, db_type, host, port, database_name, username, password, connection_url, enabled, created_at, updated_at
- [x] 1.5 Add database constraint for single default provider (CHECK constraint or trigger)
- [x] 1.6 Add indexes: llm_providers(is_default), llm_providers(enabled), external_tools(enabled), external_tools(tool_type)

## 2. Data Migration

- [x] 2.1 Write migration function to copy settings where setting_type='llm_provider' to llm_providers table
- [x] 2.2 Write migration function to copy settings where setting_type='tool' to external_tools table
- [x] 2.3 Write migration function to copy settings where setting_type='database' to database_configs table
- [x] 2.4 Add validation during migration to catch malformed configs
- [x] 2.5 Wrap migration in transaction with rollback on error
- [x] 2.6 Add migration verification step to compare record counts

## 3. Backend Models

- [x] 3.1 Create LLMProvider model in server/app/models/llm_provider.py
- [x] 3.2 Create ExternalTool model in server/app/models/external_tool.py
- [x] 3.3 Create DatabaseConfig model in server/app/models/database_config.py
- [x] 3.4 Update server/app/models/__init__.py to export new models

## 4. Pydantic Validation Schemas

- [x] 4.1 Create server/app/schemas/llm_config.py with OpenAIConfig model
- [x] 4.2 Add AnthropicConfig model with api_key validation
- [x] 4.3 Add AzureConfig model with deployment and base_url validation
- [x] 4.4 Add CustomConfig model with base_url requirement
- [x] 4.5 Create discriminated union type LLMProviderConfig
- [x] 4.6 Add validator for Azure base_url to check .openai.azure.com suffix

## 5. Repository Updates

- [x] 5.1 Update SettingRepository.get_by_type() to query new tables based on type
- [x] 5.2 Update SettingRepository.get_by_type_and_id() to query new tables
- [x] 5.3 Update SettingRepository.create() to insert into appropriate table
- [x] 5.4 Update SettingRepository.update() to update appropriate table
- [x] 5.5 Update SettingRepository.delete() to delete from appropriate table
- [x] 5.6 Update encryption/decryption methods to work with new table columns
- [x] 5.7 Update get_default_provider() to query llm_providers.is_default
- [x] 5.8 Update set_default_provider() to update llm_providers.is_default

## 6. Encryption Key Management

- [x] 6.1 Update server/app/core/encryption.py _initialize() to check ENVIRONMENT env var
- [x] 6.2 Add production mode check: raise ValueError if ENCRYPTION_KEY not set
- [x] 6.3 Update development mode warning with prominent borders and key display
- [x] 6.4 Add key generation command to error message for production failures

## 7. LLM Provider API Endpoints

- [x] 7.1 Update POST /settings/llm-providers to use Pydantic validation before saving
- [x] 7.2 Update PUT /settings/llm-providers/{id} to use Pydantic validation
- [x] 7.3 Update DELETE /settings/llm-providers/{id} to implement auto-promotion logic
- [x] 7.4 Add logging for auto-promotion events with old and new default provider names
- [x] 7.5 Update GET /settings/llm-providers/{id}/models to ensure it's GET not POST
- [x] 7.6 Update test_llm_provider() to work with new table structure

## 8. External Tools API Endpoints

- [x] 8.1 Update GET /settings/tools to query external_tools table
- [x] 8.2 Replace POST /settings/tools/{id}/test stub with real HTTP GET implementation
- [x] 8.3 Add 5-second timeout to connection tests
- [x] 8.4 Update tool record with last_test_at and last_test_status after test
- [x] 8.5 Return actual HTTP status and error messages in test response
- [x] 8.6 Add error handling for timeout, connection refused, and HTTP errors

## 9. Database Configuration Cleanup

- [x] 9.1 Remove GET /settings/databases endpoint from server/app/api/v1/endpoints/settings.py
- [x] 9.2 Remove PUT /settings/databases/{id} endpoint
- [x] 9.3 Remove POST /settings/databases/{id}/test endpoint
- [x] 9.4 Remove database configuration schemas from server/app/schemas/case.py
- [x] 9.5 Remove getDatabases() from src/lib/api.ts
- [x] 9.6 Remove updateDatabase() from src/lib/api.ts
- [x] 9.7 Remove testDatabase() from src/lib/api.ts

## 10. Frontend Fixes

- [x] 10.1 Fix src/lib/api.ts fetchModels() to remove method: 'POST' (use GET)
- [x] 10.2 Update fetchModels() to extract models from response.models
- [x] 10.3 Verify settingsStore.fetchModels() works with updated API

## 11. Testing

- [ ] 11.1 Test LLM provider CRUD operations with new schema
- [ ] 11.2 Test encryption/decryption with new table columns
- [ ] 11.3 Test default provider auto-promotion on deletion
- [ ] 11.4 Test Pydantic validation for all provider types (OpenAI, Anthropic, Azure, Custom)
- [ ] 11.5 Test Azure validation rejects base_url without .openai.azure.com
- [ ] 11.6 Test encryption key fails fast in production mode
- [ ] 11.7 Test tool connection testing returns real HTTP results
- [ ] 11.8 Test model discovery uses GET method
- [ ] 11.9 Verify database configuration endpoints are removed

## 12. Deployment

- [ ] 12.1 Backup production database before deployment
- [ ] 12.2 Run migration on staging environment first
- [ ] 12.3 Verify ENCRYPTION_KEY is set in production environment
- [ ] 12.4 Deploy application with new code
- [ ] 12.5 Monitor logs for errors during 24-48 hour validation period
- [ ] 12.6 Verify all settings are accessible and functional
- [ ] 12.7 Drop old settings table after validation period
- [ ] 12.8 Update deployment documentation with encryption key requirements
