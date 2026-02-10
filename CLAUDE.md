# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AIOps intelligent diagnosis platform with a React + TypeScript frontend and FastAPI backend. The system provides real-time agent-based problem diagnosis through WebSocket communication, featuring multi-agent collaboration, hypothesis trees, topology graphs, and knowledge management.

## Development Commands

### Frontend (React + Vite + TypeScript)

```bash
# Install dependencies
pnpm install --prefer-offline

# Development server with HMR
pnpm dev

# Build for production (disables source identifiers)
pnpm build:prod

# Lint code
pnpm lint

# Preview production build
pnpm preview
```

### Backend (FastAPI)

```bash
cd server

# Install dependencies
pip install -r requirements.txt

# Start infrastructure (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Run database migrations
psql -U postgres -d aiops -f migrations/001_create_diagnosis_tables.sql

# Initialize database (creates default users)
python init_db.py

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (required for diagnosis tasks)
celery -A app.core.celery_app worker --loglevel=info

# Start production server (4 workers)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Default users after `init_db.py`:
- admin / admin123 (管理员)
- engineer / engineer123 (工程师)
- viewer / viewer123 (观察者)

### Production Deployment

```bash
# Start all services with Docker Compose
cd server && docker-compose up -d

# Check service health
curl http://localhost:8000/api/v1/health/db
curl http://localhost:8000/api/v1/health/redis
curl http://localhost:8000/api/v1/health/celery

# Monitor Celery tasks
celery -A app.core.celery_app inspect active
celery -A app.core.celery_app inspect stats

# View logs
tail -f server/logs/aiops.log
docker-compose logs -f celery_worker

# Database rollback (if needed)
psql -U postgres -d aiops -f migrations/001_rollback.sql
```

## Critical Production Requirements

**IMPORTANT:** The diagnosis system requires ALL of the following to function:
1. **PostgreSQL** - State persistence and event sourcing
2. **Redis** - Session management and Pub/Sub messaging
3. **Celery Worker** - Background task processing for diagnosis workflows
4. **LLM API Keys** - At least one provider (Anthropic or OpenAI) configured

Without Celery workers running, diagnosis tasks will queue indefinitely and never execute.

## OpenSpec Workflow

- Follow the standard OpenSpec flow: exploration → artifacts (proposal, design, specs, tasks) → implementation → archive
- Sync delta specs to main before archiving changes
- Mark tasks complete only after testing integration

## Code Quality for Commercial Software

- Always verify imports are correct after multi-file changes, especially when moving or renaming modules
- Run type checking (mypy for Python, tsc for TypeScript) before marking implementation complete
- Test integration points between backend and frontend after making changes to both
- Verify WebSocket message flow end-to-end when modifying real-time features
- Check Celery task execution when modifying diagnosis workflows
- Test with real LLM providers, not just mocks, before production deployment

## Change Scope

- Prioritize production stability over feature additions
- When modifying core workflows (diagnosis, agents, state management), test thoroughly with all components running
- Database schema changes require migration scripts in `server/migrations/`
- API changes must maintain backward compatibility or require version bumps

## Architecture

### State Management (Zustand)

The application uses Zustand for global state management with two main stores:

- **diagnosisStore** (`src/store/diagnosisStore.ts`): Manages diagnosis cases, WebSocket connections, agent messages, timeline updates, and action proposals. Handles real-time communication with the backend agent system.

- **authStore** (`src/store/authStore.ts`): Manages authentication state, user sessions, and JWT tokens stored in localStorage.

### WebSocket Communication

Real-time agent communication is handled through `src/lib/websocket.ts` (WebSocketService class):

- Connects to `ws://localhost:8000/api/v1/agent/ws`
- Implements automatic reconnection with exponential backoff (max 5 attempts)
- Message types: `agent_message`, `action_proposal`, `diagnosis_status`, `timeline_update`, `confidence_update`, `confirmation_required`, `error`
- The diagnosisStore subscribes to WebSocket messages and updates UI state accordingly

### API Layer

REST API client in `src/lib/api.ts` provides typed interfaces for:
- Authentication (login, register, logout, getCurrentUser)
- Dashboard (stats, cases, agents, system health)
- Investigation (start/stop diagnosis, action approval/rejection)
- Knowledge (graph, historical cases)
- Settings (redlines, tools, masking rules)

All requests include JWT token from localStorage in Authorization header.

### Routing

React Router v6 with protected routes (`src/App.tsx`):
- `/login` - Public login page
- `/dashboard` - Main dashboard with stats and recent cases
- `/investigation` - Active diagnosis investigation view
- `/investigation/:id` - Specific case investigation
- `/knowledge` - Knowledge graph and historical cases
- `/settings` - System configuration

Protected routes check authentication via authStore before rendering.

### Component Organization

- **pages/**: Top-level route components (Dashboard, Investigation, Knowledge, Settings, Login)
- **components/dashboard/**: Dashboard-specific components (CaseList, StatCard, SystemHealthCard)
- **components/investigation/**: Investigation UI (AgentCollaborationPanel, DiagnosisTimeline, HypothesisTree, TopologyGraph, EvidencePanel, ActionProposalBar, ConfirmationDialog)
- **components/knowledge/**: Knowledge management (KnowledgeGraph, HistoricalCases, SearchBar)
- **components/settings/**: Settings UI (ToolList, RedlineList, MaskingRules)
- **components/common/**: Reusable UI components (Button, Card, Modal, Badge, Tabs, StatusIcon)

### Type System

All TypeScript types are centralized in `src/types/`:
- `agent.ts` - Agent definitions and roles
- `investigation.ts` - Investigation, evidence, hypothesis types
- `dashboard.ts` - Dashboard stats and case types
- `knowledge.ts` - Knowledge graph and historical case types
- `settings.ts` - Configuration types
- `index.ts` - Re-exports all types

### Styling

- **Tailwind CSS** with custom configuration (`tailwind.config.js`)
- Custom color palette defined in `src/constants/colors.ts`
- Radix UI components for accessible primitives
- Theme support via `next-themes`

### Backend Structure

Production-ready FastAPI backend with distributed task processing:

**Core Infrastructure:**
- `app/core/celery_app.py` - Celery configuration for distributed tasks
- `app/core/redis_client.py` - Redis connection pool (singleton)
- `app/core/session_manager.py` - Redis-backed session management
- `app/core/event_publisher.py` - Redis Pub/Sub event publishing
- `app/core/event_subscriber.py` - Redis Pub/Sub event subscription
- `app/core/llm_factory.py` - Multi-provider LLM factory with fallback
- `app/core/tool_registry.py` - Tool registration and agent-tool mapping
- `app/core/database.py` - PostgreSQL connection with async support

**Agent System:**
- `app/services/agents/base_agent.py` - BaseAgent with timeout and retry logic
- `app/services/agents/coordinator_agent.py` - Orchestration agent
- `app/services/agents/log_agent.py` - Log analysis agent
- `app/services/agents/code_agent.py` - Code analysis agent
- `app/services/agents/knowledge_agent.py` - Knowledge graph agent
- `app/services/agents/metric_agent.py` - Metrics analysis agent

**Workflow & State:**
- `app/services/workflow_engine.py` - LangGraph workflow orchestration
- `app/services/state_manager.py` - Hybrid state management (memory + snapshots + events)
- `app/tasks/diagnosis_tasks.py` - Celery tasks for async diagnosis

**API & WebSocket:**
- `app/api/v1/endpoints/websocket.py` - WebSocket with Redis Pub/Sub integration
- `app/api/v1/endpoints/investigation.py` - REST API for diagnosis control
- `app/api/v1/endpoints/health.py` - Health checks for Celery, Redis, PostgreSQL

**Tools:**
- `app/tools/base_tools.py` - ELK query, Git search, DB query tools
- `app/schemas/events.py` - Event type definitions for event sourcing

### Multi-Agent Architecture

**LangChain 0.3+ Integration:**
- Agents use `langchain_core.tools.BaseTool` for tool integration
- LLM provider abstraction supports OpenAI, Anthropic, Azure OpenAI
- Automatic fallback chain with retry logic and exponential backoff
- Token usage tracking and cost estimation

**LangGraph 0.2+ Workflows:**
- Simple mode: Centralized coordination with sequential execution
- Complex mode: StateGraph DAG with parallel execution and conditional routing
- Workflow control: pause, resume, cancel operations
- Event publication at node entry/exit for observability

**State Management:**
- In-memory: Active workflow state for fast access
- Snapshots: Periodic persistence to PostgreSQL JSONB columns
- Event sourcing: Complete event log with sequence numbers and causal tracking
- State recovery: Replay events from snapshots for fault tolerance

**Distributed Task Processing:**
- Celery 5.4+ with Redis broker for background task execution
- Task retry with exponential backoff (max 3 retries)
- Task timeout handling (default 30 minutes)
- Progress publishing to Redis Pub/Sub for real-time updates
- Task result persistence to agent_executions table

**Real-Time Communication:**
- WebSocket connections with Redis Pub/Sub for multi-instance support
- Session-based event subscription on diagnosis start
- Heartbeat mechanism (30s intervals) for connection keep-alive
- Automatic event forwarding from Redis to WebSocket clients
- Connection recovery with missed event replay

## Important Patterns

### WebSocket Lifecycle

1. diagnosisStore calls `initializeWebSocket()` on mount
2. WebSocketService connects and subscribes to message handlers
3. When diagnosis starts, `startDiagnosis()` sends REST API call then WebSocket message
4. Backend streams updates via WebSocket (agent messages, timeline, confidence)
5. UI updates reactively through Zustand state changes
6. On unmount, call `disconnectWebSocket()` to cleanup

### Action Approval Flow

1. Backend sends `action_proposal` message via WebSocket
2. diagnosisStore sets `proposedAction` state
3. ActionProposalBar component renders with approve/reject buttons
4. User clicks approve → `approveAction()` → WebSocket sends `approve_action`
5. Backend executes action and sends result

### Path Aliases

TypeScript path alias `@/*` maps to `./src/*` (configured in `tsconfig.json` and `vite.config.ts`).

## Environment Variables

Frontend (`.env`):
- `VITE_API_BASE_URL` - Backend API URL (default: `http://localhost:8000/api/v1`)

Backend (`server/.env`) - **REQUIRED for production**:
```bash
# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Redis (REQUIRED)
REDIS_URL=redis://localhost:6379/0

# Celery (REQUIRED)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_TIMEOUT=1800

# LLM Providers (at least one REQUIRED)
LLM_PRIMARY_PROVIDER=anthropic  # or 'openai'
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Security (REQUIRED - generate secure random key)
SECRET_KEY=your-secure-random-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (REQUIRED for production)
CORS_ORIGINS=http://localhost:5173,https://your-domain.com

# Logging
LOG_LEVEL=INFO  # Use INFO or WARNING in production
LOG_FILE=logs/aiops.log

# Agent Configuration
USE_REAL_AGENTS=true  # Set to false for testing without LLM calls
```

**Critical:** Database configuration (PostgreSQL and Redis) is managed exclusively through environment variables for security. There is no UI for database configuration. All connection settings must be in `server/.env` before starting.

## Backend API Documentation

When server is running, access interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting Production Issues

### Diagnosis Not Starting
1. Check Celery worker is running: `celery -A app.core.celery_app inspect active`
2. Verify Redis connection: `curl http://localhost:8000/api/v1/health/redis`
3. Check LLM API keys are valid in `.env`
4. Review logs: `tail -f server/logs/aiops.log`

### WebSocket Connection Failures
1. Verify Redis Pub/Sub is working: `redis-cli PUBSUB CHANNELS`
2. Check WebSocket endpoint logs for connection errors
3. Ensure CORS_ORIGINS includes frontend URL
4. Test WebSocket directly: `wscat -c ws://localhost:8000/api/v1/agent/ws`

### Database Migration Issues
1. Check current schema: `psql -U postgres -d aiops -c "\dt"`
2. Verify migration was applied: Check `diagnosis_sessions`, `diagnosis_events`, `agent_executions` tables exist
3. Rollback if needed: `psql -U postgres -d aiops -f migrations/001_rollback.sql`
4. Reapply: `psql -U postgres -d aiops -f migrations/001_create_diagnosis_tables.sql`

### Celery Task Stuck
1. Check task status: `celery -A app.core.celery_app inspect active`
2. View task details: `celery -A app.core.celery_app inspect stats`
3. Purge queue if needed: `celery -A app.core.celery_app purge`
4. Restart worker: `docker-compose restart celery_worker`

## Logging

The backend uses Python's standard logging module with both console and file output. See `server/LOGGING.md` for detailed configuration.

Key log locations:
- Authentication events (login, logout, token validation)
- WebSocket connections and message flow
- Diagnosis agent workflow execution
- API endpoint access and errors
- Permission checks and authorization failures
- LLM API calls and token usage
- Celery task lifecycle events

View logs in real-time:
```bash
tail -f server/logs/aiops.log
docker-compose logs -f celery_worker
```

## Production Monitoring

Key metrics to monitor:
- Celery task queue length (should be near zero)
- Task execution time (diagnosis tasks: 30s-5min typical)
- Redis memory usage (monitor for memory leaks)
- PostgreSQL connection pool utilization
- WebSocket connection count
- LLM API latency and error rates
- Event sourcing table growth rate
