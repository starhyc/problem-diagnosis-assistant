## 1. Infrastructure Setup

- [x] 1.1 Add dependencies to requirements.txt (langchain, langgraph, celery, redis, psycopg2-binary, langchain-openai, langchain-anthropic)
- [x] 1.2 Create docker-compose.yml with PostgreSQL, Redis, and Celery worker services
- [x] 1.3 Update server/app/core/config.py with PostgreSQL, Redis, and LLM provider settings
- [x] 1.4 Create .env.example with all required environment variables
- [x] 1.5 Write deployment documentation in server/DEPLOYMENT.md

## 2. Database Migration

- [x] 2.1 Create PostgreSQL migration script in server/migrations/001_create_diagnosis_tables.sql
- [x] 2.2 Add diagnosis_sessions table with JSONB snapshot_data column
- [x] 2.3 Add diagnosis_events table with sequence number and JSONB event_data
- [x] 2.4 Add agent_executions table for tracking agent performance
- [x] 2.5 Create migration script to copy existing SQLite data to PostgreSQL
- [x] 2.6 Update server/app/core/database.py to support PostgreSQL connection
- [x] 2.7 Add database health check endpoint

## 3. Redis Integration

- [x] 3.1 Create server/app/core/redis_client.py with Redis connection pool
- [x] 3.2 Implement RedisSessionManager in server/app/core/session_manager.py
- [x] 3.3 Add session CRUD operations (create, get, update, delete with TTL)
- [x] 3.4 Implement Redis Pub/Sub publisher in server/app/core/event_publisher.py
- [x] 3.5 Implement Redis Pub/Sub subscriber in server/app/core/event_subscriber.py
- [x] 3.6 Add Redis health check and connection retry logic

## 4. LLM Provider System

- [x] 4.1 Create server/app/core/llm_factory.py with LLMFactory class
- [x] 4.2 Implement OpenAI provider support with ChatOpenAI
- [x] 4.3 Implement Anthropic provider support with ChatAnthropic
- [x] 4.4 Implement Azure OpenAI provider support with AzureChatOpenAI
- [x] 4.5 Add provider fallback chain logic with retry mechanism
- [x] 4.6 Implement token usage tracking and cost estimation
- [x] 4.7 Add provider configuration validation

## 5. Tool Registry System

- [x] 5.1 Create server/app/core/tool_registry.py with ToolRegistry singleton
- [x] 5.2 Implement tool registration with validation
- [x] 5.3 Add agent-tool mapping configuration in database
- [x] 5.4 Create base tool implementations (ELK query, Git search, DB query)
- [x] 5.5 Implement get_tools_for_agent method with caching
- [x] 5.6 Add tool execution monitoring and metrics

## 6. State Management System

- [x] 6.1 Create server/app/services/state_manager.py with StateManager class
- [x] 6.2 Implement in-memory state storage with DiagnosisState model
- [x] 6.3 Add snapshot creation logic at workflow node completion
- [x] 6.4 Implement event recording to diagnosis_events table
- [x] 6.5 Add state recovery from snapshots and event replay
- [x] 6.6 Implement state query methods (current state, historical state)

## 7. LangChain Agent Implementation

- [x] 7.1 Create server/app/services/agents/base_agent.py with BaseAgent class
- [x] 7.2 Implement CoordinatorAgent in server/app/services/agents/coordinator_agent.py
- [x] 7.3 Implement LogAgent in server/app/services/agents/log_agent.py
- [x] 7.4 Implement CodeAgent in server/app/services/agents/code_agent.py
- [x] 7.5 Implement KnowledgeAgent in server/app/services/agents/knowledge_agent.py
- [x] 7.6 Implement MetricAgent in server/app/services/agents/metric_agent.py
- [x] 7.7 Add agent error handling and timeout logic

## 8. Workflow Orchestration

- [x] 8.1 Create server/app/services/workflow_engine.py with DiagnosisWorkflowEngine
- [x] 8.2 Define DiagnosisState TypedDict with all required fields
- [x] 8.3 Implement create_simple_workflow for centralized coordination
- [x] 8.4 Implement create_complex_workflow with LangGraph StateGraph
- [x] 8.5 Add workflow nodes for each agent and coordinator
- [x] 8.6 Implement conditional edges based on confidence and evidence
- [x] 8.7 Add workflow mode selection logic (simple vs complex)
- [x] 8.8 Implement workflow pause, resume, and cancel operations

## 9. Celery Task Processing

- [x] 9.1 Create server/app/core/celery_app.py with Celery configuration
- [x] 9.2 Implement run_diagnosis Celery task in server/app/tasks/diagnosis_tasks.py
- [x] 9.3 Add task retry logic with exponential backoff
- [x] 9.4 Implement task timeout handling (30 minute default)
- [x] 9.5 Add task result persistence to database
- [x] 9.6 Implement task progress publishing to Redis Pub/Sub
- [x] 9.7 Add Celery worker monitoring and health checks

## 10. WebSocket Enhancement

- [x] 10.1 Update server/app/api/v1/endpoints/websocket.py with Redis Pub/Sub integration
- [x] 10.2 Replace in-memory ConnectionManager with Redis-backed session management
- [x] 10.3 Implement event subscription on diagnosis start
- [x] 10.4 Add event forwarding from Redis Pub/Sub to WebSocket clients
- [x] 10.5 Implement connection recovery and missed event replay
- [x] 10.6 Add heartbeat/ping mechanism for connection keep-alive
- [x] 10.7 Update message handlers to submit Celery tasks instead of direct execution

## 11. Event-Driven Communication

- [x] 11.1 Define event types in server/app/schemas/events.py
- [x] 11.2 Implement event publication in workflow nodes
- [x] 11.3 Add event persistence to diagnosis_events table
- [x] 11.4 Implement event ordering with sequence numbers
- [x] 11.5 Add causal relationship tracking (parent event IDs)
- [x] 11.6 Implement event filtering and routing logic

## 12. API Updates

- [x] 12.1 Update server/app/api/v1/endpoints/investigation.py to use new agent system
- [x] 12.2 Add session_id to API responses (replace client_id)
- [x] 12.3 Update error responses with retry information
- [x] 12.4 Add new endpoints for task status and result retrieval
- [x] 12.5 Maintain backward compatibility with existing message types
- [x] 12.6 Update API documentation in server/docs/

## 13. Testing

- [ ] 13.1 Create integration tests for LangChain agents in server/tests/test_agents.py
- [ ] 13.2 Add workflow engine tests with mock agents
- [ ] 13.3 Create Celery task tests with Redis mock
- [ ] 13.4 Add state management tests (snapshots + events)
- [ ] 13.5 Create WebSocket integration tests with Redis Pub/Sub
- [ ] 13.6 Add LLM provider fallback tests
- [ ] 13.7 Create load tests for multiple workers and instances

## 14. Migration and Rollout

- [x] 14.1 Add feature flag for switching between mock and real agents
- [x] 14.2 Create database migration scripts with rollback procedures
- [x] 14.3 Write runbook for deployment in server/RUNBOOK.md
- [x] 14.4 Set up monitoring dashboards for Celery, Redis, and PostgreSQL
- [x] 14.5 Create alerting rules for task failures and timeouts
- [ ] 14.6 Perform canary deployment to 10% of traffic
- [ ] 14.7 Monitor metrics and gradually increase to 100%

## 15. Documentation

- [x] 15.1 Update server/README.md with new architecture overview
- [x] 15.2 Document LLM provider configuration in server/docs/LLM_PROVIDERS.md
- [x] 15.3 Create tool development guide in server/docs/TOOL_DEVELOPMENT.md
- [x] 15.4 Document workflow customization in server/docs/WORKFLOWS.md
- [x] 15.5 Update CLAUDE.md with new architecture patterns
- [x] 15.6 Create troubleshooting guide in server/docs/TROUBLESHOOTING.md
