# AIOps Intelligent Diagnosis Platform - Backend

Production-ready multi-agent diagnosis system built with FastAPI, LangChain, and Celery.

## Architecture

### Core Components

- **FastAPI**: High-performance web framework with WebSocket support
- **LangChain 0.3+**: Multi-agent orchestration framework
- **LangGraph 0.2+**: Workflow state management
- **Celery 5.4+**: Distributed task processing
- **Redis 7**: Session management and Pub/Sub messaging
- **PostgreSQL 16**: State persistence with JSONB support
- **SQLAlchemy**: ORM with async support

### Multi-Agent System

Five specialized agents collaborate on diagnosis:

1. **CoordinatorAgent**: Orchestrates workflow and synthesizes results
2. **LogAgent**: Analyzes ELK logs for error patterns
3. **CodeAgent**: Searches code repositories and traces call chains
4. **KnowledgeAgent**: Queries knowledge graph for similar cases
5. **MetricAgent**: Analyzes monitoring data and metrics

### LLM Provider Support

Multi-provider configuration with automatic fallback:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Azure OpenAI

## Quick Start

### Using Docker Compose

```bash
cd server
docker-compose up -d
```

This starts PostgreSQL, Redis, and Celery worker.

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run migrations:
```bash
psql -U postgres -d aiops -f migrations/001_create_diagnosis_tables.sql
```

4. Start services:
```bash
# Terminal 1: API server
uvicorn main:app --reload

# Terminal 2: Celery worker
celery -A app.core.celery_app worker --loglevel=info
```

## Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/aiops

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM Providers
LLM_PRIMARY_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_TASK_TIMEOUT=1800
```

See `.env.example` for complete configuration.

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API Guide: [docs/API.md](docs/API.md)

## WebSocket Communication

Real-time diagnosis updates via WebSocket at `/api/v1/agent/ws`:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/agent/ws');

ws.send(JSON.stringify({
  type: 'start_diagnosis',
  data: { symptom: 'Order service timeout', mode: 'complex' }
}));
```

## State Management

Hybrid approach combining:
- **In-memory**: Active workflow state
- **Snapshots**: Periodic state persistence to PostgreSQL
- **Event sourcing**: Complete event log for replay

## Workflow Modes

### Simple Mode
Centralized coordination with sequential agent execution.

### Complex Mode
LangGraph-based DAG with parallel execution and conditional routing.

## Monitoring

Health check endpoints:
- `/health/db` - PostgreSQL status
- `/health/redis` - Redis connectivity
- `/health/celery` - Worker status

## Development

See additional documentation:
- [LLM Providers](docs/LLM_PROVIDERS.md)
- [Tool Development](docs/TOOL_DEVELOPMENT.md)
- [Workflow Customization](docs/WORKFLOWS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Deployment Guide](DEPLOYMENT.md)

## License

MIT License
