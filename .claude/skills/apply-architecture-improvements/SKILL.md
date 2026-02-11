---
name: apply-architecture-improvements
description: This skill should be used when the user asks to "apply architecture improvements", "improve project A", "migrate patterns from project B", "adopt best practices", "refactor based on analysis", or wants to implement architectural patterns extracted from analysis documentation.
version: 0.1.0
---

# Apply Architecture Improvements

## Purpose

Apply architectural patterns, design improvements, and best practices from analysis documentation to an existing project. Focus on incremental, safe improvements that maintain backward compatibility while enhancing code quality, maintainability, and scalability.

## When to Use This Skill

Use this skill when:
- Applying patterns extracted from project analysis
- Migrating architectural improvements to current project
- Refactoring based on documented best practices
- Implementing LLM integration patterns
- Adopting real-time communication designs
- Improving state management architecture
- Enhancing code organization and structure

## Prerequisites

**Required before starting:**
1. Architecture analysis documentation (from analyze-project-architecture skill)
2. Clear understanding of current project structure
3. Identified improvement areas
4. User approval for scope of changes

## Improvement Workflow

### Phase 1: Assessment and Planning

**Analyze current project state:**
1. Read existing architecture and code organization
2. Identify gaps between current state and target patterns
3. Assess compatibility and prerequisites
4. Determine improvement priorities

**Create improvement plan:**
1. List specific improvements to implement
2. Order by dependencies and risk level
3. Identify potential breaking changes
4. Plan rollback strategies

**Get user approval:**
```
Use AskUserQuestion to present plan:
- What will be changed
- Why these changes improve the codebase
- What risks exist
- What order to implement
```

### Phase 2: Incremental Implementation

**Follow safe refactoring principles:**
- Make one logical change at a time
- Keep tests passing after each change
- Commit frequently with clear messages
- Verify functionality after each step

**Implementation order (low to high risk):**
1. Add new abstractions without changing existing code
2. Migrate usage to new abstractions incrementally
3. Remove old implementations once fully migrated
4. Refactor internal implementations

### Phase 3: Pattern Migration

**For each pattern to migrate:**

#### LLM Integration Improvements

**Multi-Provider Abstraction:**
1. Create provider interface/abstract class
2. Implement provider-specific classes
3. Create factory for provider instantiation
4. Add fallback chain logic
5. Migrate existing LLM calls to use factory
6. Add configuration for provider selection

**Example approach:**
```typescript
// Step 1: Create interface (new file)
interface LLMProvider {
  generate(prompt: string): Promise<string>;
  stream(prompt: string): AsyncIterator<string>;
}

// Step 2: Implement providers (new files)
class OpenAIProvider implements LLMProvider { ... }
class AnthropicProvider implements LLMProvider { ... }

// Step 3: Create factory (new file)
class LLMFactory {
  static create(provider: string): LLMProvider { ... }
}

// Step 4: Migrate usage (edit existing files)
// Before: const response = await openai.complete(prompt);
// After: const llm = LLMFactory.create('openai');
//        const response = await llm.generate(prompt);
```

**Token Management:**
1. Create token tracking service
2. Add token counting utilities
3. Implement usage limits
4. Add cost calculation
5. Integrate with existing LLM calls

**Streaming Response Handler:**
1. Create stream processing utility
2. Add chunk accumulation logic
3. Implement error handling
4. Update UI components for streaming
5. Migrate existing calls to use streaming

#### Real-Time Communication Improvements

**WebSocket Manager:**
1. Create WebSocketManager class
2. Implement connection lifecycle methods
3. Add message routing
4. Implement reconnection logic
5. Migrate existing WebSocket code
6. Add event subscription system

**Message Protocol:**
1. Define message type interfaces
2. Create message validation
3. Implement type-safe handlers
4. Add message serialization
5. Update existing message handling

**Pub/Sub Architecture:**
1. Set up Redis client
2. Create event publisher service
3. Create event subscriber service
4. Define channel naming conventions
5. Migrate to pub/sub for multi-instance support

#### State Management Improvements

**Centralized Store:**
1. Choose state library (Zustand/Redux)
2. Define state shape
3. Create store with actions
4. Add selectors
5. Migrate component state to store
6. Remove local state where appropriate

**State Persistence:**
1. Create persistence middleware
2. Add serialization logic
3. Implement hydration on startup
4. Configure what to persist
5. Test persistence across sessions

**Event Sourcing:**
1. Define event types
2. Create event store
3. Implement event append logic
4. Add state reconstruction
5. Migrate critical state to event sourcing

#### Code Organization Improvements

**Module Restructuring:**
1. Plan new directory structure
2. Create new directories
3. Move files incrementally
4. Update imports after each move
5. Verify tests pass after each move

**Service Layer:**
1. Identify business logic in controllers/components
2. Create service classes
3. Move business logic to services
4. Update controllers/components to use services
5. Add dependency injection if needed

**Repository Pattern:**
1. Create repository interfaces
2. Implement repositories for data access
3. Move database queries to repositories
4. Update services to use repositories
5. Remove direct database access from services

### Phase 4: Testing and Validation

**After each change:**
1. Run existing tests
2. Test affected functionality manually
3. Check for regressions
4. Verify performance hasn't degraded
5. Review error handling

**Integration testing:**
1. Test end-to-end workflows
2. Verify real-time features work
3. Test error scenarios
4. Check edge cases
5. Validate with production-like data

### Phase 5: Documentation and Cleanup

**Update documentation:**
1. Update README with new patterns
2. Document new abstractions
3. Add migration guides for team
4. Update API documentation
5. Add inline comments for complex logic

**Code cleanup:**
1. Remove dead code
2. Remove unused imports
3. Consolidate duplicated logic
4. Standardize naming conventions
5. Format code consistently

## Implementation Strategies

### Strangler Fig Pattern

**For large refactorings:**
1. Create new implementation alongside old
2. Route new code to new implementation
3. Gradually migrate existing code
4. Remove old implementation when fully migrated

**Example:**
```typescript
// Phase 1: Add new alongside old
const oldLLM = new OpenAIClient();
const newLLM = LLMFactory.create('openai');

// Phase 2: Route new code to new implementation
if (useNewImplementation) {
  return await newLLM.generate(prompt);
} else {
  return await oldLLM.complete(prompt);
}

// Phase 3: Migrate gradually
// Convert one feature at a time to use newLLM

// Phase 4: Remove old
// Delete oldLLM and useNewImplementation flag
```

### Feature Flags

**For risky changes:**
1. Add feature flag configuration
2. Implement new feature behind flag
3. Test with flag enabled
4. Gradually roll out
5. Remove flag when stable

### Adapter Pattern

**For incompatible interfaces:**
1. Create adapter class
2. Implement interface translation
3. Use adapter to bridge old and new
4. Migrate incrementally
5. Remove adapter when migration complete

## Risk Management

### Identify High-Risk Changes

**High risk indicators:**
- Changes to authentication/authorization
- Database schema modifications
- Breaking API changes
- State management overhauls
- Real-time communication changes

**Mitigation strategies:**
- Implement behind feature flags
- Add comprehensive tests
- Deploy to staging first
- Have rollback plan ready
- Monitor closely after deployment

### Rollback Planning

**For each major change:**
1. Document current state
2. Create rollback procedure
3. Test rollback procedure
4. Keep rollback simple (revert commits)
5. Monitor for issues requiring rollback

### Backward Compatibility

**Maintain compatibility:**
- Keep old interfaces during migration
- Add deprecation warnings
- Provide migration path
- Document breaking changes
- Version APIs appropriately

## Common Improvement Patterns

### Pattern: Add LLM Provider Abstraction

**Steps:**
1. Create `src/lib/llm/` directory
2. Create `src/lib/llm/types.ts` with interface
3. Create `src/lib/llm/providers/openai.ts`
4. Create `src/lib/llm/providers/anthropic.ts`
5. Create `src/lib/llm/factory.ts`
6. Update existing LLM calls to use factory
7. Add configuration for provider selection

**Files to create:**
- `src/lib/llm/types.ts`
- `src/lib/llm/factory.ts`
- `src/lib/llm/providers/openai.ts`
- `src/lib/llm/providers/anthropic.ts`

**Files to modify:**
- Existing files with LLM calls
- Configuration files

### Pattern: Add WebSocket Manager

**Steps:**
1. Create `src/lib/websocket/` directory
2. Create `src/lib/websocket/manager.ts`
3. Create `src/lib/websocket/types.ts` for message types
4. Implement connection lifecycle
5. Add reconnection logic
6. Add message routing
7. Migrate existing WebSocket code

**Files to create:**
- `src/lib/websocket/manager.ts`
- `src/lib/websocket/types.ts`

**Files to modify:**
- Components using WebSocket
- Store files handling WebSocket state

### Pattern: Add State Persistence

**Steps:**
1. Create `src/lib/storage/` directory
2. Create `src/lib/storage/persistence.ts`
3. Add serialization utilities
4. Create store middleware for auto-save
5. Add hydration on app startup
6. Configure what to persist

**Files to create:**
- `src/lib/storage/persistence.ts`

**Files to modify:**
- Store configuration files
- App initialization code

### Pattern: Restructure into Service Layer

**Steps:**
1. Create `src/services/` directory
2. Identify business logic in components
3. Create service classes
4. Move business logic to services
5. Update components to use services
6. Add dependency injection if needed

**Files to create:**
- `src/services/[domain]Service.ts` for each domain

**Files to modify:**
- Components with business logic
- API client files

## Best Practices

### Code Quality

**Maintain standards:**
- Follow existing code style
- Use consistent naming conventions
- Add types for new code (TypeScript)
- Keep functions small and focused
- Avoid premature optimization

### Testing

**Test coverage:**
- Add tests for new abstractions
- Update tests for modified code
- Test error scenarios
- Test edge cases
- Integration test critical paths

### Communication

**Keep team informed:**
- Document changes in commit messages
- Update team documentation
- Share migration guides
- Announce breaking changes
- Provide examples of new patterns

### Incremental Progress

**Small, safe steps:**
- One logical change per commit
- Keep changes reviewable
- Deploy frequently
- Monitor after each deployment
- Iterate based on feedback

## Additional Resources

### Reference Files

For detailed implementation guides:
- **`references/implementation-guides.md`** - Step-by-step guides for common patterns
- **`references/migration-strategies.md`** - Strategies for safe migration

### Examples

Working examples in `examples/`:
- **`example-llm-migration/`** - Complete LLM abstraction migration
- **`example-websocket-refactor/`** - WebSocket manager implementation

## Troubleshooting

### Common Issues

**Import errors after restructuring:**
- Update all import paths
- Use IDE refactoring tools
- Search for old import patterns
- Run type checker to find issues

**Tests failing after changes:**
- Update test mocks
- Fix test data
- Update assertions
- Check for timing issues

**Performance degradation:**
- Profile before and after
- Check for N+1 queries
- Optimize hot paths
- Add caching if needed

**Breaking changes:**
- Add backward compatibility layer
- Provide migration script
- Document breaking changes
- Version appropriately

## Success Criteria

Improvement is successful when:
- All tests pass
- No regressions in functionality
- Code is more maintainable
- Patterns are consistently applied
- Team understands new patterns
- Documentation is updated
- Performance is maintained or improved
