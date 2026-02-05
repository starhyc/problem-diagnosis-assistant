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

# Build for development
pnpm build

# Build for production (disables source identifiers)
pnpm build:prod

# Lint code
pnpm lint

# Preview production build
pnpm preview

# Clean dependencies and cache
pnpm clean
```

### Backend (FastAPI)

```bash
cd server

# Install dependencies
pip install -r requirements.txt

# Initialize database (creates tables and default users)
python init_db.py

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Default users after `init_db.py`:
- admin / admin123 (管理员)
- engineer / engineer123 (工程师)
- viewer / viewer123 (观察者)

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

Backend (`server/.env`):
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT signing key (must be changed in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time
- `CORS_ORIGINS` - Allowed frontend origins
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FILE` - Log file path (default: `logs/aiops.log`)

## Backend API Documentation

When server is running, access interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Logging

The backend uses Python's standard logging module with both console and file output. See `server/LOGGING.md` for detailed configuration.

Key log locations:
- Authentication events (login, logout, token validation)
- WebSocket connections and message flow
- Diagnosis agent workflow
- API endpoint access
- Permission checks

View logs in real-time:
```bash
tail -f logs/aiops.log
```
