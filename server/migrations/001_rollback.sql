-- Rollback script for diagnosis tables
-- Run this to revert the migration

-- Drop tables in reverse order of creation
DROP TABLE IF EXISTS agent_executions;
DROP TABLE IF EXISTS diagnosis_events;
DROP TABLE IF EXISTS diagnosis_sessions;

-- Recreate original SQLite-compatible schema if needed
-- (Add your original schema here if rolling back to SQLite)
