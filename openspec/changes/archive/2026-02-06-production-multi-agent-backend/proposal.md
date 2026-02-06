## Why

The current backend uses mock agents with hardcoded diagnosis flows, making it unsuitable for production use. We need a production-ready multi-agent architecture using LangChain/LangGraph that can handle real-world diagnostic scenarios with reliable state management, distributed task processing, and real-time communication at scale.

## What Changes

- Replace mock agents with LangChain-based multi-agent system (Coordinator, Log, Code, Knowledge, Metric agents)
- Implement LangGraph workflow engine with support for both centralized coordination (simple tasks) and DAG-based orchestration (complex tasks)
- Add Celery + Redis for distributed async task processing with WebSocket real-time updates via Redis Pub/Sub
- Migrate from SQLite to PostgreSQL with hybrid state management (in-memory runtime + snapshots + event sourcing)
- Implement tool registry system for agent-tool mapping and configuration
- Add multi-LLM provider support (OpenAI, Anthropic, Azure) with fallback capabilities
- Implement Redis-based session management for horizontal scalability
- Add comprehensive error handling, retry mechanisms, and monitoring

## Capabilities

### New Capabilities
- `langchain-agent-system`: Multi-agent collaboration framework with LangChain/LangGraph integration
- `workflow-orchestration`: Dual-mode workflow engine (centralized coordinator + LangGraph DAG)
- `tool-registry`: Centralized tool registration and agent-tool mapping system
- `distributed-task-processing`: Celery-based async task queue with Redis broker
- `realtime-communication`: WebSocket + Redis Pub/Sub for real-time diagnosis updates
- `state-management`: Hybrid state persistence (memory + snapshots + event sourcing)
- `session-management`: Redis-based session storage for multi-instance deployment
- `multi-llm-provider`: Configurable LLM provider factory with fallback support

### Modified Capabilities
- `diagnosis-workflow`: Requirements change from mock hardcoded flow to dynamic LangGraph-based workflows
- `agent-communication`: Requirements change from simple message passing to structured event-driven architecture

## Impact

**Backend Services:**
- `server/app/services/` - Complete rewrite of agent system
- `server/app/api/v1/endpoints/websocket.py` - Enhanced with Redis Pub/Sub integration
- `server/app/core/` - New modules for Celery, Redis, LLM factory

**Database:**
- Migration from SQLite to PostgreSQL
- New tables: `diagnosis_sessions`, `diagnosis_events`, `agent_executions`
- Enhanced existing tables with JSONB fields for complex state

**Infrastructure:**
- New dependencies: Celery, Redis, LangChain, LangGraph, psycopg2
- New services: Redis server, Celery workers, PostgreSQL database
- Configuration: Environment variables for LLM providers, Redis, PostgreSQL

**API Contracts:**
- WebSocket message types extended with new event types
- Session management changes (client_id → session_id with Redis)
- Enhanced error responses with retry information
