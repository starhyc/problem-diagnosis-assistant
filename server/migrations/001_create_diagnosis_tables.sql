-- Migration: Create diagnosis tables for production multi-agent backend
-- Version: 001
-- Description: Creates tables for diagnosis sessions, events, and agent executions

-- Diagnosis sessions table (snapshots)
CREATE TABLE IF NOT EXISTS diagnosis_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    snapshot_data JSONB NOT NULL,
    snapshot_version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_diagnosis_sessions_session_id ON diagnosis_sessions(session_id);
CREATE INDEX idx_diagnosis_sessions_created_at ON diagnosis_sessions(created_at);

-- Diagnosis events table (event sourcing)
CREATE TABLE IF NOT EXISTS diagnosis_events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    sequence INT NOT NULL,
    parent_event_id INT,
    timestamp TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, sequence),
    FOREIGN KEY (parent_event_id) REFERENCES diagnosis_events(id) ON DELETE SET NULL
);

CREATE INDEX idx_diagnosis_events_session_id ON diagnosis_events(session_id);
CREATE INDEX idx_diagnosis_events_timestamp ON diagnosis_events(timestamp);
CREATE INDEX idx_diagnosis_events_event_type ON diagnosis_events(event_type);

-- Agent executions table (performance tracking)
CREATE TABLE IF NOT EXISTS agent_executions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    execution_time_ms INT,
    error_message TEXT,
    metadata JSONB,
    FOREIGN KEY (session_id) REFERENCES diagnosis_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX idx_agent_executions_session_id ON agent_executions(session_id);
CREATE INDEX idx_agent_executions_agent_type ON agent_executions(agent_type);
CREATE INDEX idx_agent_executions_status ON agent_executions(status);
