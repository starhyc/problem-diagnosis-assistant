## Context

The current backend uses `MockDiagnosisAgent` with hardcoded diagnosis flows that simulate agent behavior through predefined message sequences. This approach is unsuitable for production as it cannot handle real diagnostic scenarios, lacks state persistence, and doesn't scale beyond a single instance.

**Current State:**
- Mock agents with hardcoded responses in `server/app/services/diagnosis_agent.py`
- SQLite database with basic models (User, Case, Agent)
- Simple WebSocket ConnectionManager with in-memory client dictionary
- No distributed task processing or state recovery
- Single LLM provider support (if any)

**Constraints:**
- Must maintain backward compatibility with existing WebSocket message types
- Frontend expects specific event formats (agent_message, timeline_update, etc.)
- Zero-downtime migration required for production deployment
- Must support horizontal scaling for multiple FastAPI instances

**Stakeholders:**
- Backend team (implementation)
- Frontend team (API contract changes)
- DevOps (infrastructure deployment)
- End users (no service interruption)

## Goals / Non-Goals

**Goals:**
- Replace mock agents with production-ready LangChain/LangGraph multi-agent system
- Enable distributed task processing with Celery + Redis for horizontal scalability
- Implement hybrid state management (memory + snapshots + event sourcing) for reliability
- Support real-time updates via WebSocket + Redis Pub/Sub across multiple instances
- Provide multi-LLM provider support with automatic fallback
- Migrate to PostgreSQL for production-grade persistence

**Non-Goals:**
- Changing frontend UI components or user experience
- Implementing new diagnosis algorithms or domain logic
- Adding authentication/authorization changes
- Performance optimization beyond architectural improvements
- Supporting databases other than PostgreSQL (SQLite only for local dev)

## Decisions

### Decision 1: LangGraph for workflow orchestration

**Choice:** Use LangGraph state machines for complex diagnosis workflows, with fallback to simple coordinator pattern for basic tasks.

**Rationale:**
- LangGraph provides visual workflow representation and conditional branching
- State machine model naturally fits diagnosis phases (symptom analysis → evidence collection → hypothesis verification → conclusion)
- Supports both sequential and parallel agent execution
- Built-in state persistence and recovery

**Alternatives considered:**
- Pure LangChain agents: Lacks structured workflow control, harder to visualize
- Custom workflow engine: Reinventing the wheel, maintenance burden
- Always use simple coordinator: Insufficient for complex multi-phase diagnosis

**Implementation:**
```python
# server/app/services/workflow_engine.py
from langgraph.graph import StateGraph

class DiagnosisWorkflowEngine:
    def create_simple_workflow(self) -> Runnable:
        # Coordinator → Single Agent → Done
        pass

    def create_complex_workflow(self) -> Runnable:
        workflow = StateGraph(DiagnosisState)
        workflow.add_node("coordinator", coordinator_agent)
        workflow.add_node("parallel_analysis", parallel_agents)
        workflow.add_conditional_edges(...)
        return workflow.compile()
```

### Decision 2: Celery + Redis for distributed task processing

**Choice:** Use Celery with Redis broker for async task queue, Redis Pub/Sub for real-time event streaming.

**Rationale:**
- Celery provides mature distributed task processing with retry, timeout, and monitoring
- Redis serves triple duty: Celery broker, Pub/Sub for WebSocket events, session storage
- Decouples WebSocket handlers from long-running diagnosis tasks
- Enables horizontal scaling of both FastAPI instances and Celery workers

**Alternatives considered:**
- RabbitMQ as broker: More complex setup, Redis sufficient for our needs
- ARQ (async queue): Lighter but less mature, fewer features
- Direct WebSocket execution: Blocks connection, no recovery on disconnect

**Architecture:**
```
WebSocket Request → FastAPI Handler → Celery Task Queue
                         ↓                    ↓
                    Subscribe to         Worker executes
                    Redis Pub/Sub        LangGraph workflow
                         ↓                    ↓
                    Forward events ← Publish to Redis Pub/Sub
                         ↓
                    Client receives real-time updates
```

### Decision 3: Hybrid state management (memory + snapshots + events)

**Choice:** Maintain runtime state in memory, save snapshots at workflow nodes, record all events to PostgreSQL.

**Rationale:**
- In-memory state provides fast access during execution
- Snapshots enable quick recovery without full event replay
- Event sourcing provides complete audit trail and debugging capability
- Balances performance (memory), recovery speed (snapshots), and auditability (events)

**Alternatives considered:**
- Pure event sourcing: Slow recovery, requires full replay
- Only snapshots: Loses granular history, harder to debug
- Only in-memory: No persistence, lost on crash

**Database schema:**
```sql
-- Snapshots for fast recovery
CREATE TABLE diagnosis_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    snapshot_data JSONB NOT NULL,
    snapshot_version INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Events for audit trail and replay
CREATE TABLE diagnosis_events (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    sequence INT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, sequence)
);
```

### Decision 4: Tool registry pattern for agent-tool mapping

**Choice:** Centralized ToolRegistry singleton with database-backed agent-tool configuration.

**Rationale:**
- Decouples tools from agents, enabling dynamic reconfiguration
- Supports tool reuse across multiple agents
- Configuration stored in database allows runtime updates
- Simplifies testing by mocking tool registry

**Alternatives considered:**
- Hardcoded tools per agent: Inflexible, requires code changes
- Plugin system: Over-engineered for current needs
- Tool discovery: Too magical, harder to debug

**Implementation:**
```python
# server/app/core/tool_registry.py
class ToolRegistry:
    _instance = None
    _tools: Dict[str, BaseTool] = {}
    _agent_tool_map: Dict[str, List[str]] = {}

    def register_tool(self, name: str, tool: BaseTool):
        self._tools[name] = tool

    def get_tools_for_agent(self, agent_type: str) -> List[BaseTool]:
        tool_names = self._agent_tool_map.get(agent_type, [])
        return [self._tools[name] for name in tool_names]
```

### Decision 5: Multi-LLM provider factory with fallback

**Choice:** LLMFactory with configurable primary/fallback provider chain.

**Rationale:**
- Avoids vendor lock-in, enables cost optimization
- Automatic fallback improves reliability
- Different agents can use different providers based on requirements
- Supports gradual migration between providers

**Alternatives considered:**
- Single provider: Vendor lock-in, no fallback
- Manual provider selection per request: Complex API, error-prone
- Load balancing across providers: Unnecessary complexity

**Configuration:**
```python
# server/app/core/config.py
llm_config = {
    "primary": {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "api_key": env.ANTHROPIC_API_KEY
    },
    "fallback": {
        "provider": "openai",
        "model": "gpt-4-turbo",
        "api_key": env.OPENAI_API_KEY
    }
}
```

### Decision 6: PostgreSQL with JSONB for complex state

**Choice:** Migrate from SQLite to PostgreSQL, use JSONB columns for hypothesis trees, evidence lists, and workflow state.

**Rationale:**
- PostgreSQL supports concurrent writes (SQLite doesn't)
- JSONB provides flexible schema for evolving state structures
- Native JSON operators enable efficient queries on nested data
- Production-grade reliability and performance

**Alternatives considered:**
- Keep SQLite: Insufficient for multi-instance deployment
- MongoDB: Adds complexity, PostgreSQL JSONB sufficient
- Separate columns for each field: Rigid schema, harder to evolve

### Decision 7: Redis session management for horizontal scaling

**Choice:** Store all WebSocket session data in Redis with 1-hour TTL.

**Rationale:**
- Enables session access across multiple FastAPI instances
- Automatic expiration prevents memory leaks
- Fast in-memory access for session lookups
- Supports reconnection to different instance

**Alternatives considered:**
- In-memory sessions: Doesn't scale horizontally
- Database sessions: Too slow for real-time lookups
- Sticky sessions: Complicates load balancing, reduces flexibility

## Risks / Trade-offs

**[Risk] LangChain/LangGraph API changes**
→ **Mitigation:** Pin specific versions (langchain==0.3.x, langgraph==0.2.x), abstract LangGraph behind internal interfaces

**[Risk] Redis single point of failure**
→ **Mitigation:** Use Redis Sentinel for high availability, implement graceful degradation (fallback to in-memory sessions)

**[Risk] Celery worker crashes lose in-flight tasks**
→ **Mitigation:** Task acknowledgment only after completion, automatic requeue on worker failure, workflow state snapshots enable resume

**[Risk] PostgreSQL migration downtime**
→ **Mitigation:** Blue-green deployment, run both databases in parallel during migration, rollback plan

**[Risk] Increased infrastructure complexity**
→ **Mitigation:** Docker Compose for local dev, comprehensive deployment documentation, health checks for all services

**[Risk] LLM provider rate limits or outages**
→ **Mitigation:** Automatic fallback to secondary provider, exponential backoff with jitter, circuit breaker pattern

**[Trade-off] Event sourcing increases storage**
→ **Accepted:** Storage is cheap, auditability is critical for production diagnosis system

**[Trade-off] Celery adds latency vs direct execution**
→ **Accepted:** ~100-200ms overhead acceptable for long-running diagnosis tasks (minutes), enables reliability and scaling

**[Trade-off] Redis dependency increases operational complexity**
→ **Accepted:** Redis is industry-standard, benefits (scaling, pub/sub, sessions) outweigh operational cost

## Migration Plan

**Phase 1: Infrastructure Setup (Week 1)**
1. Deploy PostgreSQL database
2. Deploy Redis instance
3. Set up Celery workers
4. Update environment configuration

**Phase 2: Database Migration (Week 1-2)**
1. Create new PostgreSQL tables (diagnosis_sessions, diagnosis_events, agent_executions)
2. Migrate existing SQLite data to PostgreSQL
3. Run dual-write to both databases for validation
4. Switch reads to PostgreSQL
5. Deprecate SQLite

**Phase 3: Core Services Implementation (Week 2-3)**
1. Implement LLMFactory and multi-provider support
2. Implement ToolRegistry and register existing tools
3. Implement RedisSessionManager
4. Update WebSocket handler with Redis Pub/Sub

**Phase 4: Agent System (Week 3-4)**
1. Implement base LangChain agents (Coordinator, Log, Code, Knowledge, Metric)
2. Implement simple workflow engine (coordinator pattern)
3. Implement LangGraph complex workflow
4. Implement WorkflowEngine with mode selection logic

**Phase 5: Task Processing (Week 4-5)**
1. Implement Celery tasks for diagnosis execution
2. Integrate workflow engine with Celery workers
3. Implement state management (snapshots + events)
4. Add retry and timeout handling

**Phase 6: Testing & Rollout (Week 5-6)**
1. Integration testing with real LLM providers
2. Load testing with multiple workers and instances
3. Canary deployment to 10% of traffic
4. Monitor metrics and error rates
5. Gradual rollout to 100%

**Rollback Strategy:**
- Keep mock agent code for 2 weeks post-deployment
- Feature flag to switch between mock and real agents
- Database rollback scripts prepared
- Redis flush procedure documented

## Open Questions

**Q1: Should we implement agent memory/context across diagnosis sessions?**
- Current design: Each diagnosis session is independent
- Alternative: Maintain agent memory across sessions for learning
- Decision needed: Discuss with product team on value vs complexity

**Q2: What's the optimal snapshot frequency?**
- Current design: Snapshot at each workflow node completion
- Alternative: Time-based snapshots (every 30s) or event-count based (every 10 events)
- Decision needed: Performance testing to determine optimal strategy

**Q3: Should we support custom agent types via configuration?**
- Current design: Five hardcoded agents (Coordinator, Log, Code, Knowledge, Metric)
- Alternative: Plugin system for custom agents
- Decision needed: Wait for user feedback before adding complexity

**Q4: How to handle partial diagnosis results on timeout?**
- Current design: Return partial results with confidence score
- Alternative: Mark as failed and require restart
- Decision needed: UX team input on user expectations
