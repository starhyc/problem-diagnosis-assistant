# Deployment Runbook

## Pre-Deployment Checklist

- [ ] All environment variables configured in `.env`
- [ ] Database migrations tested
- [ ] LLM provider API keys validated
- [ ] Redis and PostgreSQL accessible
- [ ] Celery worker tested locally

## Deployment Steps

### 1. Database Setup

```bash
# Create database
psql -U postgres -c "CREATE DATABASE aiops;"

# Run migrations
psql -U postgres -d aiops -f migrations/001_create_diagnosis_tables.sql

# Verify tables
psql -U postgres -d aiops -c "\dt"
```

### 2. Start Infrastructure

```bash
cd server
docker-compose up -d postgres redis
```

### 3. Deploy Application

```bash
# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Start Celery worker (separate terminal)
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

### 4. Verify Health

```bash
curl http://localhost:8000/health/db
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/celery
```

### 5. Enable Real Agents

```bash
# Update .env
USE_REAL_AGENTS=true

# Restart services
```

## Rollback Procedure

### If deployment fails:

```bash
# 1. Disable real agents
USE_REAL_AGENTS=false

# 2. Rollback database
psql -U postgres -d aiops -f migrations/001_rollback.sql

# 3. Restart services
docker-compose restart
```

## Monitoring

### Check Celery Tasks

```bash
celery -A app.core.celery_app inspect active
celery -A app.core.celery_app inspect stats
```

### Check Logs

```bash
tail -f logs/aiops.log
docker-compose logs -f celery
```

### Check Redis

```bash
redis-cli INFO stats
redis-cli PUBSUB CHANNELS
```

## Troubleshooting

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.

## Post-Deployment

- [ ] Verify WebSocket connections
- [ ] Test diagnosis workflow end-to-end
- [ ] Monitor error rates
- [ ] Check LLM token usage
- [ ] Verify event persistence
