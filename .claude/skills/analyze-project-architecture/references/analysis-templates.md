# Analysis Templates

## Architecture Overview Template

```markdown
# [Project Name] Architecture Overview

## System Architecture

**Type:** [Frontend/Backend/Full-stack]
**Primary Language:** [TypeScript/Python/etc.]
**Framework:** [React/FastAPI/etc.]

### Component Diagram
[Textual description of major components and their relationships]

### Key Components
1. **Component Name** (`path/to/component`)
   - Responsibility: [What it does]
   - Dependencies: [What it depends on]
   - Interfaces: [How others interact with it]

### Data Flow
[Describe how data flows through the system]

### Technology Stack
- Frontend: [Technologies]
- Backend: [Technologies]
- Database: [Technologies]
- Infrastructure: [Technologies]

### Architectural Decisions
- **Decision:** [What was decided]
- **Rationale:** [Why this approach]
- **Trade-offs:** [Pros and cons]
```

## LLM Integration Template

```markdown
# LLM Integration Patterns

## Provider Abstraction

**Location:** `path/to/llm/factory.ts`

### Architecture
[Describe the abstraction pattern]

### Supported Providers
- Provider 1: [Details]
- Provider 2: [Details]

### Code Example
[Actual code snippet from the project]

### Fallback Strategy
[How fallback is implemented]

### Token Management
- Tracking: [How tokens are tracked]
- Limits: [How limits are enforced]
- Cost estimation: [How costs are calculated]

## Streaming Implementation

**Location:** `path/to/streaming.ts`

### Pattern
[Describe streaming pattern]

### Code Example
[Actual code snippet]

### Error Handling
[How streaming errors are handled]

## Prompt Engineering

### Template System
[How prompts are templated]

### Context Management
[How context window is managed]

### Examples
[Actual prompt examples from the project]
```

## Real-Time Communication Template

```markdown
# Real-Time Communication Architecture

## WebSocket Implementation

**Location:** `path/to/websocket.ts`

### Connection Management
- Initialization: [How connections are established]
- Lifecycle: [Connection lifecycle management]
- Cleanup: [How connections are cleaned up]

### Code Example
[Actual WebSocket setup code]

### Message Protocol

**Message Types:**
| Type | Direction | Purpose | Payload |
|------|-----------|---------|---------|
| type1 | client→server | [Purpose] | [Structure] |
| type2 | server→client | [Purpose] | [Structure] |

### Reconnection Strategy
- Trigger: [When reconnection happens]
- Backoff: [Exponential backoff details]
- Max attempts: [Limit]

### Code Example
[Actual reconnection code]

## State Synchronization

### Pattern
[Describe how state is kept in sync]

### Conflict Resolution
[How conflicts are handled]

### Code Example
[Actual sync code]

## Pub/Sub Architecture

**Technology:** [Redis/RabbitMQ/etc.]
**Location:** `path/to/pubsub.ts`

### Channel Design
[How channels are organized]

### Event Publishing
[How events are published]

### Event Subscription
[How events are subscribed to]

### Code Example
[Actual pub/sub code]
```

## State Management Template

```markdown
# State Management Architecture

## Store Architecture

**Library:** [Zustand/Redux/etc.]
**Location:** `path/to/store.ts`

### Store Structure
[Describe store organization]

### State Shape
[Document state structure]

### Actions/Mutations
[List key actions]

### Code Example
[Actual store code]

## Persistence Strategy

### Storage Backend
[LocalStorage/SessionStorage/Database]

### Serialization
[How state is serialized]

### Hydration
[How state is restored]

### Code Example
[Actual persistence code]

## Event Sourcing

**Location:** `path/to/events.ts`

### Event Types
[List event types]

### Event Store
[How events are stored]

### State Reconstruction
[How state is rebuilt from events]

### Code Example
[Actual event sourcing code]

## Optimistic Updates

### Pattern
[Describe optimistic update pattern]

### Rollback Strategy
[How failed updates are rolled back]

### Code Example
[Actual optimistic update code]
```

## Best Practices Template

```markdown
# Best Practices Extracted

## Code Organization

### Module Structure
- Pattern: [Describe pattern]
- Benefits: [Why this works]
- Example: [File structure example]

### Dependency Management
- Pattern: [Describe pattern]
- Benefits: [Why this works]
- Example: [Code example]

## Error Handling

### Strategy
[Describe error handling approach]

### Patterns
1. **Pattern Name**
   - Use case: [When to use]
   - Implementation: [How it's done]
   - Example: [Code snippet]

## Testing

### Strategy
[Describe testing approach]

### Patterns
[Testing patterns used]

### Coverage
[What's tested and how]

## Security

### Authentication
[Auth patterns]

### Authorization
[Authz patterns]

### Data Protection
[How sensitive data is protected]

### Input Validation
[Validation patterns]

## Performance

### Optimization Techniques
[List techniques used]

### Caching Strategy
[Caching patterns]

### Lazy Loading
[Lazy loading patterns]

## Deployment

### CI/CD Pipeline
[Pipeline structure]

### Environment Management
[How environments are managed]

### Monitoring
[What's monitored and how]
```

## Quick Analysis Checklist

Use this checklist to ensure comprehensive analysis:

### Architecture
- [ ] System architecture documented
- [ ] Component responsibilities identified
- [ ] Data flow mapped
- [ ] Technology stack listed
- [ ] Architectural decisions documented

### LLM Integration (if applicable)
- [ ] Provider abstraction analyzed
- [ ] Token management documented
- [ ] Streaming implementation reviewed
- [ ] Prompt patterns extracted
- [ ] Error handling documented

### Real-Time Features (if applicable)
- [ ] WebSocket implementation analyzed
- [ ] Message protocol documented
- [ ] Reconnection strategy reviewed
- [ ] State sync patterns extracted
- [ ] Pub/Sub architecture documented

### State Management
- [ ] Store architecture documented
- [ ] Persistence strategy analyzed
- [ ] Event sourcing reviewed (if used)
- [ ] Optimistic updates documented (if used)

### Code Quality
- [ ] Organization patterns extracted
- [ ] Error handling patterns documented
- [ ] Testing strategy reviewed
- [ ] Security patterns identified
- [ ] Performance optimizations noted

### Infrastructure
- [ ] Database schema reviewed
- [ ] Caching strategy documented
- [ ] Background jobs analyzed (if used)
- [ ] Deployment architecture documented
- [ ] Monitoring approach reviewed
