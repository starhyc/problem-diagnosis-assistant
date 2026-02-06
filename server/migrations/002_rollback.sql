-- Rollback: Simplify LLM provider model from primary/fallback to default
-- Date: 2026-02-06

-- Step 1: Drop unique constraint
DROP INDEX IF EXISTS idx_settings_default_per_type;

-- Step 2: Restore is_primary and is_fallback to config JSON
UPDATE settings
SET config = jsonb_set(
    jsonb_set(
        config::jsonb,
        '{is_primary}',
        to_jsonb(is_default)
    ),
    '{is_fallback}',
    'false'::jsonb
)
WHERE type = 'llm_provider';

-- Step 3: Drop is_default column
ALTER TABLE settings DROP COLUMN IF EXISTS is_default;
