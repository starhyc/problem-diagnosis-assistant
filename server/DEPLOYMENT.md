# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- PostgreSQL 16+
- Redis 7+
- Python 3.11+

## Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Update the following required variables in `.env`:
```bash
# Database
DATABASE_URL=postgresql://aiops:aiops_password@localhost:5432/aiops

# LLM API Keys (at least one required)
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# Security
SECRET_KEY=generate-a-secure-random-key
```

## Local Development with Docker Compose

1. Start all services:
```bash
cd server
docker-compose up -d
```

2. Run database migrations:
```bash
python migrations/001_create_diagnosis_tables.sql
```

3. Start the FastAPI server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Start Celery worker:
```bash
celery -A app.core.celery_app worker --loglevel=info
```

## Production Deployment

### 1. Infrastructure Setup

Deploy the following services:
- PostgreSQL 16+ (managed service recommended)
- Redis 7+ (with persistence enabled)
- Load balancer for FastAPI instances

### 2. Database Migration

```bash
# Run migration script
psql $DATABASE_URL -f migrations/001_create_diagnosis_tables.sql
```

### 3. Deploy FastAPI Instances

```bash
# Install dependencies
pip install -r requirements.txt

# Run with multiple workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Deploy Celery Workers

```bash
# Start multiple workers for horizontal scaling
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

### 5. Health Checks

- FastAPI: `GET /health`
- Database: `GET /api/v1/health/db`
- Redis: `GET /api/v1/health/redis`
- Celery: Monitor via Flower or Celery events

## Rollback Procedure

1. Stop new traffic to updated instances
2. Revert to previous Docker image/code version
3. If database migration was applied, run rollback script:
```bash
psql $DATABASE_URL -f migrations/rollback_001.sql
```

## Monitoring

Key metrics to monitor:
- Celery task queue length
- Task execution time
- Redis memory usage
- PostgreSQL connection pool
- WebSocket connection count
- LLM API latency and errors
