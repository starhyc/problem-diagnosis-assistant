# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints require JWT authentication via Bearer token in Authorization header.

## Investigation Endpoints

### GET /investigation
Get investigation data including agents, topology, and sample logs.

**Response:**
```json
{
  "agents": [{"id": "coordinator", "name": "协调Agent", "role": "Coordinator", "color": "#3b82f6"}],
  "sample_logs": "...",
  "topology_nodes": [...],
  "topology_edges": [...],
  "hypothesis_tree": {...}
}
```

### POST /investigation/start
Start a new diagnosis session.

**Request:**
```json
{
  "problem_description": "Order service timeout",
  "mode": "simple"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "task_id": "celery-task-id",
  "status": "submitted"
}
```

### POST /investigation/stop
Stop a running diagnosis.

**Request:**
```json
{
  "session_id": "uuid"
}
```

### GET /investigation/task/{task_id}
Get Celery task status and results.

**Response:**
```json
{
  "task_id": "uuid",
  "status": "PROGRESS|SUCCESS|FAILURE",
  "result": {...},
  "info": {...}
}
```

## WebSocket

### WS /agent/ws
Real-time diagnosis updates via WebSocket.

**Client → Server Messages:**
- `start_diagnosis`: Start diagnosis
- `stop_diagnosis`: Stop diagnosis
- `approve_action`: Approve proposed action
- `reject_action`: Reject proposed action
- `pause_diagnosis`: Pause workflow
- `resume_diagnosis`: Resume workflow

**Server → Client Messages:**
- `connection_established`: Connection confirmed with session_id
- `diagnosis_started`: Diagnosis task submitted
- `agent_message`: Agent output
- `diagnosis_status`: Status update
- `heartbeat`: Keep-alive ping (every 30s)

## Health Endpoints

### GET /health/db
Database health check.

### GET /health/redis
Redis health check.

### GET /health/celery
Celery worker health check.

### GET /health/celery/tasks
Celery task statistics.
