-- Migration: Simplify LLM provider model from primary/fallback to default
-- Date: 2026-02-06

-- Step 1: Add is_default column
ALTER TABLE settings ADD COLUMN is_default BOOLEAN DEFAULT FALSE;

-- Step 2: Migrate existing data (set is_default = is_primary)
UPDATE settings
SET is_default = (config::json->>'is_primary')::boolean
WHERE type = 'llm_provider'
  AND config::json->>'is_primary' IS NOT NULL;

-- Step 3: Ensure at least one provider is default if any exist
DO $$
DECLARE
    provider_count INTEGER;
    default_count INTEGER;
    first_provider_id VARCHAR;
BEGIN
    SELECT COUNT(*) INTO provider_count FROM settings WHERE type = 'llm_provider';
    SELECT COUNT(*) INTO default_count FROM settings WHERE type = 'llm_provider' AND is_default = TRUE;

    IF provider_count > 0 AND default_count = 0 THEN
        SELECT setting_id INTO first_provider_id FROM settings WHERE type = 'llm_provider' LIMIT 1;
        UPDATE settings SET is_default = TRUE WHERE setting_id = first_provider_id;
    END IF;
END $$;

-- Step 4: Add unique constraint (only one default per type)
CREATE UNIQUE INDEX idx_settings_default_per_type
ON settings (type, is_default)
WHERE is_default = TRUE;

-- Step 5: Update config JSON to remove is_primary and is_fallback
UPDATE settings
SET config = (
    SELECT jsonb_build_object(
        'provider', config::jsonb->'provider',
        'api_key', config::jsonb->'api_key',
        'base_url', config::jsonb->'base_url',
        'models', config::jsonb->'models',
        'enabled', config::jsonb->'enabled'
    )
)
WHERE type = 'llm_provider';
