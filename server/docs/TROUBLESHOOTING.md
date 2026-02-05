# Troubleshooting Guide

## Common Issues

### Celery Worker Not Starting

**Symptoms:**
- Tasks stuck in PENDING state
- No worker logs

**Solutions:**
```bash
# Check Redis connectivity
redis-cli ping

# Check Celery configuration
celery -A app.core.celery_app inspect active

# Restart worker with verbose logging
celery -A app.core.celery_app worker --loglevel=debug
```

### WebSocket Connection Failures

**Symptoms:**
- Frontend shows "Connection failed"
- No real-time updates

**Solutions:**
```bash
# Check Redis Pub/Sub
redis-cli
> SUBSCRIBE diagnosis:*

# Verify WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://localhost:8000/api/v1/agent/ws
```

### LLM Provider Errors

**Symptoms:**
- "No LLM provider available"
- API key errors

**Solutions:**
```bash
# Verify API keys in .env
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Test provider directly
python -c "from app.core.llm_factory import llm_factory; print(llm_factory.create_with_fallback())"
```

### Database Connection Issues

**Symptoms:**
- "Connection refused" errors
- Migration failures

**Solutions:**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Test connection
psql -U postgres -d aiops -c "SELECT 1"

# Run migrations
psql -U postgres -d aiops -f migrations/001_create_diagnosis_tables.sql
```

### State Recovery Failures

**Symptoms:**
- Lost diagnosis state after restart
- Event replay errors

**Solutions:**
```bash
# Check diagnosis_sessions table
psql -U postgres -d aiops -c "SELECT session_id, snapshot_version FROM diagnosis_sessions"

# Check event log
psql -U postgres -d aiops -c "SELECT session_id, sequence, event_type FROM diagnosis_events ORDER BY sequence"
```

## Performance Issues

### High Memory Usage

**Causes:**
- Too many active workflows
- Large state objects

**Solutions:**
- Reduce `CELERY_WORKER_MAX_TASKS_PER_CHILD`
- Implement state cleanup for completed sessions
- Monitor with `celery -A app.core.celery_app inspect stats`

### Slow Agent Responses

**Causes:**
- LLM provider latency
- Tool execution timeouts

**Solutions:**
- Check LLM provider status
- Reduce agent timeout values
- Enable caching in tool_registry

## Debugging

### Enable Debug Logging

```bash
# .env
LOG_LEVEL=DEBUG

# View logs
tail -f logs/aiops.log
```

### Inspect Celery Tasks

```bash
# Active tasks
celery -A app.core.celery_app inspect active

# Scheduled tasks
celery -A app.core.celery_app inspect scheduled

# Task stats
celery -A app.core.celery_app inspect stats
```

### Monitor Redis

```bash
# Connection count
redis-cli INFO clients

# Memory usage
redis-cli INFO memory

# Pub/Sub channels
redis-cli PUBSUB CHANNELS
```

## Health Checks

```bash
# Database
curl http://localhost:8000/health/db

# Redis
curl http://localhost:8000/health/redis

# Celery
curl http://localhost:8000/health/celery
```

## Getting Help

1. Check logs in `logs/aiops.log`
2. Review [DEPLOYMENT.md](../DEPLOYMENT.md) for setup issues
3. Verify environment variables in `.env`
4. Test individual components in isolation
