-- Migration: workflow consistency hardening
-- Version: 003
-- Description:
--   1) Add idempotency key storage table with unique constraint.
--   2) Ensure diagnosis_events uniqueness remains enforced by (session_id, sequence).

CREATE TABLE IF NOT EXISTS diagnosis_idempotency_keys (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    action_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (session_id, action_id, step_id)
);

CREATE INDEX IF NOT EXISTS idx_diagnosis_idempotency_session_id
    ON diagnosis_idempotency_keys(session_id);

CREATE INDEX IF NOT EXISTS idx_diagnosis_idempotency_created_at
    ON diagnosis_idempotency_keys(created_at);
