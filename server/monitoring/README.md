# Monitoring Configuration

## Prometheus Metrics

Add to `docker-compose.yml`:

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - ./monitoring/grafana:/var/lib/grafana
```

## Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'celery'
    static_configs:
      - targets: ['celery:9808']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']
```

## Key Metrics to Monitor

### Celery
- Task success/failure rate
- Task execution time (p50, p95, p99)
- Active workers count
- Queue length

### Redis
- Memory usage
- Connected clients
- Pub/Sub channels
- Command latency

### PostgreSQL
- Connection pool usage
- Query execution time
- Transaction rate
- Table sizes

## Grafana Dashboards

Import dashboard IDs:
- Celery: 15902
- Redis: 11835
- PostgreSQL: 9628

## Alerting

See `monitoring/alerts.yml` for alert rules.
