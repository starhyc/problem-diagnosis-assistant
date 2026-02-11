# Architectural Pattern Catalog

Common patterns to look for when analyzing projects.

## LLM Integration Patterns

### Multi-Provider Abstraction

**Description:** Abstract LLM provider interface with multiple implementations

**Look for:**
- Factory pattern for provider creation
- Common interface across providers
- Provider-specific configuration
- Fallback chain implementation

**Files to check:**
- `**/llm/**/*.{ts,py}`
- `**/ai/**/*.{ts,py}`
- `**/providers/**/*.{ts,py}`

**Key indicators:**
- Classes/functions named `LLMFactory`, `ProviderFactory`
- Interface/abstract class named `LLMProvider`, `AIProvider`
- Configuration with provider names (openai, anthropic, etc.)

### Streaming Response Handler

**Description:** Handle streaming responses from LLM APIs

**Look for:**
- Stream processing logic
- Chunk accumulation
- Error handling during streaming
- UI updates on chunk arrival

**Files to check:**
- `**/stream/**/*.{ts,py}`
- `**/llm/**/*.{ts,py}`

**Key indicators:**
- Async generators or iterators
- Event emitters for chunks
- Buffer/accumulator variables
- `onChunk`, `onToken` callbacks

### Token Management

**Description:** Track and manage token usage and costs

**Look for:**
- Token counting logic
- Cost calculation
- Usage limits enforcement
- Token budget management

**Files to check:**
- `**/tokens/**/*.{ts,py}`
- `**/usage/**/*.{ts,py}`

**Key indicators:**
- Token counting functions
- Cost per token constants
- Usage tracking variables
- Budget limit checks

## Real-Time Communication Patterns

### WebSocket Manager

**Description:** Centralized WebSocket connection management

**Look for:**
- Singleton or service class for WebSocket
- Connection lifecycle methods
- Message routing
- Event subscription system

**Files to check:**
- `**/websocket/**/*.{ts,py}`
- `**/ws/**/*.{ts,py}`
- `**/realtime/**/*.{ts,py}`

**Key indicators:**
- Classes named `WebSocketManager`, `WSService`
- Methods: `connect`, `disconnect`, `send`, `subscribe`
- Connection state tracking
- Reconnection logic

### Reconnection Strategy

**Description:** Automatic reconnection with exponential backoff

**Look for:**
- Retry counter
- Backoff calculation
- Max retry limit
- Connection state machine

**Key indicators:**
- Variables: `retryCount`, `backoffDelay`, `maxRetries`
- Exponential calculation: `delay * 2^retryCount`
- Timeout/interval for retry attempts

### Message Protocol

**Description:** Structured message format for client-server communication

**Look for:**
- Message type definitions
- Message serialization/deserialization
- Type-safe message handling
- Message validation

**Files to check:**
- `**/types/**/*.{ts,py}`
- `**/messages/**/*.{ts,py}`
- `**/protocol/**/*.{ts,py}`

**Key indicators:**
- Type/interface definitions for messages
- Discriminated unions by message type
- Message handler maps
- Validation schemas

### Pub/Sub Architecture

**Description:** Redis or message queue for multi-instance communication

**Look for:**
- Redis pub/sub implementation
- Channel naming conventions
- Event publishing logic
- Event subscription handling

**Files to check:**
- `**/redis/**/*.{ts,py}`
- `**/pubsub/**/*.{ts,py}`
- `**/events/**/*.{ts,py}`

**Key indicators:**
- Redis client initialization
- `publish`, `subscribe` methods
- Channel name patterns
- Event forwarding logic

## State Management Patterns

### Centralized Store

**Description:** Single source of truth for application state

**Look for:**
- Store creation and configuration
- State shape definition
- Action/mutation definitions
- Selector functions

**Files to check:**
- `**/store/**/*.{ts,py}`
- `**/state/**/*.{ts,py}`

**Key indicators:**
- Store creation: `createStore`, `configureStore`
- State interfaces/types
- Action creators
- Reducers or mutations

### State Persistence

**Description:** Save and restore state across sessions

**Look for:**
- Storage backend (localStorage, sessionStorage, database)
- Serialization logic
- Hydration on app start
- Selective persistence (what to save)

**Key indicators:**
- `localStorage.setItem`, `localStorage.getItem`
- Serialization: `JSON.stringify`, `JSON.parse`
- Hydration in store initialization
- Middleware for auto-save

### Event Sourcing

**Description:** Store state changes as sequence of events

**Look for:**
- Event definitions
- Event store/log
- State reconstruction from events
- Event replay logic

**Files to check:**
- `**/events/**/*.{ts,py}`
- `**/event-store/**/*.{ts,py}`

**Key indicators:**
- Event type definitions
- Event append/log functions
- State reducer from events
- Snapshot + events pattern

### Optimistic Updates

**Description:** Update UI immediately, rollback on failure

**Look for:**
- Temporary state updates
- Rollback logic
- Conflict resolution
- Success/failure handlers

**Key indicators:**
- Temporary ID generation
- Rollback functions
- Try-catch with state revert
- Optimistic flag in state

## Background Processing Patterns

### Task Queue

**Description:** Celery, Bull, or similar for async task processing

**Look for:**
- Task definitions
- Queue configuration
- Worker setup
- Task retry logic

**Files to check:**
- `**/tasks/**/*.{ts,py}`
- `**/workers/**/*.{ts,py}`
- `**/celery/**/*.py`
- `**/bull/**/*.ts`

**Key indicators:**
- Task decorators: `@task`, `@celery.task`
- Queue creation
- Worker startup code
- Retry configuration

### Progress Tracking

**Description:** Track and report long-running task progress

**Look for:**
- Progress update mechanism
- Progress storage (Redis, database)
- Progress subscription
- UI progress display

**Key indicators:**
- Progress percentage calculation
- Progress publish/emit
- Progress polling or subscription
- Progress bar components

## API Design Patterns

### Repository Pattern

**Description:** Abstract data access layer

**Look for:**
- Repository classes
- CRUD operations
- Query methods
- Data mapping

**Files to check:**
- `**/repositories/**/*.{ts,py}`
- `**/repos/**/*.{ts,py}`

**Key indicators:**
- Classes named `*Repository`
- Methods: `find`, `findById`, `create`, `update`, `delete`
- Database abstraction

### Service Layer

**Description:** Business logic layer between API and data

**Look for:**
- Service classes
- Business logic methods
- Transaction management
- Cross-cutting concerns

**Files to check:**
- `**/services/**/*.{ts,py}`

**Key indicators:**
- Classes named `*Service`
- Business logic methods
- Repository dependencies
- Transaction decorators

### API Client

**Description:** Typed client for backend API

**Look for:**
- HTTP client wrapper
- Typed request/response
- Error handling
- Authentication injection

**Files to check:**
- `**/api/**/*.{ts,py}`
- `**/client/**/*.{ts,py}`

**Key indicators:**
- Axios/fetch wrapper
- Type definitions for endpoints
- Interceptors for auth
- Error transformation

## Security Patterns

### JWT Authentication

**Description:** Token-based authentication

**Look for:**
- Token generation
- Token validation
- Token refresh
- Token storage

**Files to check:**
- `**/auth/**/*.{ts,py}`
- `**/jwt/**/*.{ts,py}`

**Key indicators:**
- JWT library usage
- Token signing/verification
- Refresh token logic
- Token middleware

### Role-Based Access Control

**Description:** Permission system based on user roles

**Look for:**
- Role definitions
- Permission checks
- Route guards
- Middleware for authorization

**Key indicators:**
- Role enums/constants
- Permission decorators
- `hasRole`, `hasPermission` functions
- Protected route wrappers

## Database Patterns

### Migration System

**Description:** Version-controlled database schema changes

**Look for:**
- Migration files
- Migration runner
- Rollback scripts
- Schema versioning

**Files to check:**
- `**/migrations/**/*.sql`
- `**/migrations/**/*.{ts,py}`

**Key indicators:**
- Numbered migration files
- Up/down migration functions
- Migration table for tracking
- Migration CLI commands

### Connection Pooling

**Description:** Reuse database connections efficiently

**Look for:**
- Pool configuration
- Connection acquisition
- Connection release
- Pool monitoring

**Key indicators:**
- Pool size configuration
- Connection pool creation
- `acquire`/`release` methods
- Pool statistics

## Testing Patterns

### Test Fixtures

**Description:** Reusable test data and setup

**Look for:**
- Fixture definitions
- Setup/teardown functions
- Mock data generators
- Test database seeding

**Files to check:**
- `**/fixtures/**/*.{ts,py}`
- `**/test-utils/**/*.{ts,py}`

**Key indicators:**
- Fixture functions
- `beforeEach`/`afterEach` hooks
- Mock data factories
- Database seeders

### Integration Testing

**Description:** Test multiple components together

**Look for:**
- Test database setup
- API endpoint tests
- End-to-end workflows
- Test containers

**Files to check:**
- `**/*.test.{ts,py}`
- `**/*.spec.{ts,py}`
- `**/e2e/**/*.{ts,py}`

**Key indicators:**
- Database setup in tests
- HTTP request tests
- Multi-step test scenarios
- Docker test containers
