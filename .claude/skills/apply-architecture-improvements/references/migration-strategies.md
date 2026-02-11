# Migration Strategies

Safe strategies for migrating from old patterns to new architectural improvements.

## Strategy 1: Strangler Fig Pattern

### Overview
Gradually replace old system by building new system alongside it, routing traffic incrementally.

### When to Use
- Large-scale refactoring
- High-risk changes
- Systems that can't have downtime
- When you need to validate new implementation before full migration

### Implementation Steps

#### Phase 1: Establish Coexistence
```typescript
// Old implementation (keep running)
class OldLLMClient {
  async complete(prompt: string): Promise<string> {
    // Existing implementation
  }
}

// New implementation (add alongside)
class NewLLMProvider implements LLMProvider {
  async generate(prompt: string): Promise<string> {
    // New implementation
  }
}

// Router to choose between old and new
class LLMRouter {
  constructor(
    private old: OldLLMClient,
    private new: NewLLMProvider,
    private useNew: boolean = false
  ) {}

  async generate(prompt: string): Promise<string> {
    if (this.useNew) {
      return this.new.generate(prompt);
    }
    return this.old.complete(prompt);
  }
}
```

#### Phase 2: Route New Features to New Implementation
```typescript
// New features use new implementation
export function createLLMClient(feature: string): LLMRouter {
  const useNew = NEW_FEATURES.includes(feature);
  return new LLMRouter(oldClient, newProvider, useNew);
}
```

#### Phase 3: Gradually Migrate Existing Features
```typescript
// Migrate one feature at a time
const MIGRATED_FEATURES = [
  'chat',      // Week 1
  'summarize', // Week 2
  'analyze',   // Week 3
];

export function createLLMClient(feature: string): LLMRouter {
  const useNew = MIGRATED_FEATURES.includes(feature);
  return new LLMRouter(oldClient, newProvider, useNew);
}
```

#### Phase 4: Remove Old Implementation
```typescript
// Once all features migrated, remove router
export function createLLMClient(): LLMProvider {
  return new NewLLMProvider();
}

// Delete OldLLMClient and LLMRouter
```

### Benefits
- Zero downtime
- Easy rollback (flip flag)
- Validate new implementation incrementally
- Low risk

### Drawbacks
- Temporary code duplication
- Routing logic overhead
- Longer migration timeline

---

## Strategy 2: Branch by Abstraction

### Overview
Create abstraction layer, implement new version behind it, switch implementations, remove abstraction.

### When to Use
- Replacing core dependencies
- Changing data access patterns
- Swapping infrastructure components
- When you need compile-time safety during migration

### Implementation Steps

#### Phase 1: Create Abstraction
```typescript
// Create interface that both old and new can implement
interface DataStore {
  get(key: string): Promise<any>;
  set(key: string, value: any): Promise<void>;
  delete(key: string): Promise<void>;
}
```

#### Phase 2: Wrap Old Implementation
```typescript
// Adapter for old implementation
class LocalStorageAdapter implements DataStore {
  async get(key: string): Promise<any> {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : null;
  }

  async set(key: string, value: any): Promise<void> {
    localStorage.setItem(key, JSON.stringify(value));
  }

  async delete(key: string): Promise<void> {
    localStorage.removeItem(key);
  }
}
```

#### Phase 3: Migrate All Usage to Abstraction
```typescript
// Before: Direct localStorage usage
const data = JSON.parse(localStorage.getItem('key'));

// After: Use abstraction
const store: DataStore = new LocalStorageAdapter();
const data = await store.get('key');
```

#### Phase 4: Implement New Version
```typescript
// New implementation using IndexedDB
class IndexedDBAdapter implements DataStore {
  private db: IDBDatabase;

  async get(key: string): Promise<any> {
    // IndexedDB implementation
  }

  async set(key: string, value: any): Promise<void> {
    // IndexedDB implementation
  }

  async delete(key: string): Promise<void> {
    // IndexedDB implementation
  }
}
```

#### Phase 5: Switch Implementation
```typescript
// Change factory to use new implementation
export function createDataStore(): DataStore {
  // return new LocalStorageAdapter(); // Old
  return new IndexedDBAdapter(); // New
}
```

#### Phase 6: Remove Abstraction (Optional)
```typescript
// If abstraction no longer needed, inline it
const db = new IndexedDBAdapter();
await db.set('key', value);
```

### Benefits
- Type-safe migration
- All code migrated before switching
- Easy to switch back
- Clear migration boundary

### Drawbacks
- Requires abstraction design upfront
- All code must migrate before switching
- Abstraction may not fit perfectly

---

## Strategy 3: Parallel Run

### Overview
Run old and new implementations simultaneously, compare results, gradually trust new implementation.

### When to Use
- Critical business logic
- Complex algorithms
- When correctness is paramount
- When you need confidence before switching

### Implementation Steps

#### Phase 1: Run Both, Use Old
```typescript
async function processData(input: string): Promise<Result> {
  // Run old implementation (use this result)
  const oldResult = await oldProcessor.process(input);

  // Run new implementation (compare only)
  const newResult = await newProcessor.process(input);

  // Compare and log differences
  if (!deepEqual(oldResult, newResult)) {
    logger.warn('Results differ', { input, oldResult, newResult });
    metrics.increment('processor.mismatch');
  }

  // Return old result (safe)
  return oldResult;
}
```

#### Phase 2: Run Both, Use New with Fallback
```typescript
async function processData(input: string): Promise<Result> {
  try {
    // Try new implementation first
    const newResult = await newProcessor.process(input);

    // Run old for comparison
    const oldResult = await oldProcessor.process(input);

    if (!deepEqual(oldResult, newResult)) {
      logger.warn('Results differ', { input, oldResult, newResult });
      // Still use new result, but log for investigation
    }

    return newResult;
  } catch (error) {
    // Fallback to old on error
    logger.error('New processor failed, falling back', { error });
    return oldProcessor.process(input);
  }
}
```

#### Phase 3: Use New Only
```typescript
async function processData(input: string): Promise<Result> {
  return newProcessor.process(input);
}
```

### Benefits
- High confidence in new implementation
- Real-world validation
- Easy to detect regressions
- Safe rollback path

### Drawbacks
- Double computation cost
- Requires result comparison logic
- May not work for side-effect operations
- Longer migration timeline

---

## Strategy 4: Feature Flags

### Overview
Control feature rollout with runtime flags, enabling gradual rollout and quick rollback.

### When to Use
- User-facing features
- High-risk changes
- When you want gradual rollout
- When you need quick rollback capability

### Implementation Steps

#### Phase 1: Add Feature Flag System
```typescript
// Simple feature flag service
class FeatureFlags {
  private flags = new Map<string, boolean>();

  isEnabled(flag: string): boolean {
    return this.flags.get(flag) ?? false;
  }

  enable(flag: string): void {
    this.flags.set(flag, true);
  }

  disable(flag: string): void {
    this.flags.set(flag, false);
  }
}

export const featureFlags = new FeatureFlags();
```

#### Phase 2: Implement Feature Behind Flag
```typescript
async function generateResponse(prompt: string): Promise<string> {
  if (featureFlags.isEnabled('new-llm-provider')) {
    // New implementation
    const provider = LLMFactory.create({ provider: 'anthropic' });
    return provider.generate(prompt);
  } else {
    // Old implementation
    return oldLLMClient.complete(prompt);
  }
}
```

#### Phase 3: Gradual Rollout
```typescript
// Rollout to percentage of users
class FeatureFlags {
  isEnabled(flag: string, userId?: string): boolean {
    const config = this.configs.get(flag);
    if (!config) return false;

    // Percentage rollout
    if (userId && config.percentage < 100) {
      const hash = hashCode(userId);
      return (hash % 100) < config.percentage;
    }

    return config.enabled;
  }
}

// Start with 10% of users
featureFlags.setPercentage('new-llm-provider', 10);

// Increase to 50%
featureFlags.setPercentage('new-llm-provider', 50);

// Full rollout
featureFlags.setPercentage('new-llm-provider', 100);
```

#### Phase 4: Remove Flag
```typescript
// Once stable, remove flag and old code
async function generateResponse(prompt: string): Promise<string> {
  const provider = LLMFactory.create({ provider: 'anthropic' });
  return provider.generate(prompt);
}
```

### Benefits
- Quick rollback (flip flag)
- Gradual rollout
- A/B testing capability
- Production validation

### Drawbacks
- Code complexity (branching logic)
- Flag cleanup required
- Testing both paths needed

---

## Strategy 5: Database Migration Pattern

### Overview
Structured approach for database schema changes with backward compatibility.

### When to Use
- Database schema changes
- Adding/removing columns
- Changing data types
- Splitting/merging tables

### Implementation Steps

#### Phase 1: Expand (Add New Schema)
```sql
-- Add new column (nullable initially)
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT NULL;

-- Add new table
CREATE TABLE user_preferences (
  user_id INTEGER REFERENCES users(id),
  preference_key VARCHAR(255),
  preference_value TEXT,
  PRIMARY KEY (user_id, preference_key)
);
```

#### Phase 2: Migrate (Dual Write)
```typescript
// Write to both old and new
async function updateUser(userId: string, data: UserUpdate): Promise<void> {
  await db.query(
    'UPDATE users SET name = $1, email_verified = $2 WHERE id = $3',
    [data.name, data.emailVerified, userId]
  );

  // Also update old column for backward compatibility
  if (data.emailVerified !== undefined) {
    await db.query(
      'UPDATE users SET verified = $1 WHERE id = $2',
      [data.emailVerified, userId]
    );
  }
}
```

#### Phase 3: Backfill (Migrate Existing Data)
```typescript
// Backfill script
async function backfillEmailVerified(): Promise<void> {
  const users = await db.query('SELECT id, verified FROM users WHERE email_verified IS NULL');

  for (const user of users) {
    await db.query(
      'UPDATE users SET email_verified = $1 WHERE id = $2',
      [user.verified, user.id]
    );
  }
}
```

#### Phase 4: Contract (Remove Old Schema)
```sql
-- Make new column non-nullable
ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;

-- Remove old column
ALTER TABLE users DROP COLUMN verified;
```

### Benefits
- Zero downtime
- Backward compatible
- Rollback possible
- Safe for production

### Drawbacks
- Multi-step process
- Temporary data duplication
- Requires coordination

---

## Strategy 6: API Versioning

### Overview
Maintain multiple API versions during migration, deprecate old versions gradually.

### When to Use
- Public APIs
- Breaking changes
- Multiple client versions
- When you can't force immediate upgrades

### Implementation Steps

#### Phase 1: Version Existing API
```typescript
// Add version to routes
app.get('/api/v1/users', getUsersV1);
app.post('/api/v1/users', createUserV1);
```

#### Phase 2: Implement New Version
```typescript
// New version with breaking changes
app.get('/api/v2/users', getUsersV2);
app.post('/api/v2/users', createUserV2);

// V2 returns different structure
async function getUsersV2(req, res) {
  const users = await userService.getUsers();
  res.json({
    data: users.map(u => ({
      id: u.id,
      profile: { name: u.name, email: u.email },
      metadata: { createdAt: u.created_at }
    }))
  });
}
```

#### Phase 3: Deprecate Old Version
```typescript
// Add deprecation warning
app.get('/api/v1/users', (req, res, next) => {
  res.setHeader('X-API-Deprecated', 'true');
  res.setHeader('X-API-Sunset', '2026-06-01');
  next();
}, getUsersV1);
```

#### Phase 4: Remove Old Version
```typescript
// After sunset date, remove v1
app.get('/api/v1/*', (req, res) => {
  res.status(410).json({
    error: 'API version 1 has been retired. Please use /api/v2/'
  });
});
```

### Benefits
- No breaking changes for existing clients
- Clear migration path
- Gradual adoption
- Professional API management

### Drawbacks
- Maintain multiple versions
- Code duplication
- Coordination with clients needed

---

## Strategy 7: Adapter Pattern for Incremental Migration

### Overview
Create adapters to bridge old and new interfaces during migration.

### When to Use
- Incompatible interfaces
- Third-party library upgrades
- Framework migrations
- When you can't change all code at once

### Implementation Steps

#### Phase 1: Create Adapter
```typescript
// Old interface
interface OldCache {
  put(key: string, value: string): void;
  fetch(key: string): string | null;
}

// New interface
interface NewCache {
  set(key: string, value: any, ttl?: number): Promise<void>;
  get(key: string): Promise<any>;
}

// Adapter
class CacheAdapter implements OldCache {
  constructor(private newCache: NewCache) {}

  put(key: string, value: string): void {
    // Synchronous wrapper for async operation
    this.newCache.set(key, value).catch(console.error);
  }

  fetch(key: string): string | null {
    // Can't properly adapt async to sync, return null
    // This is a limitation - document it
    console.warn('Synchronous cache fetch not supported, returning null');
    return null;
  }
}
```

#### Phase 2: Use Adapter for Old Code
```typescript
// Old code continues to work
const cache: OldCache = new CacheAdapter(newRedisCache);
cache.put('key', 'value');
```

#### Phase 3: Migrate Code to New Interface
```typescript
// Gradually migrate to async interface
const cache: NewCache = newRedisCache;
await cache.set('key', 'value');
const value = await cache.get('key');
```

#### Phase 4: Remove Adapter
```typescript
// Once all code migrated, remove adapter
// Only NewCache interface remains
```

### Benefits
- Gradual migration
- Old code keeps working
- Clear migration path
- Isolated changes

### Drawbacks
- Adapter complexity
- May not perfectly bridge interfaces
- Temporary code overhead

---

## Choosing the Right Strategy

### Decision Matrix

| Scenario | Recommended Strategy | Why |
|----------|---------------------|-----|
| Large refactoring | Strangler Fig | Gradual replacement, low risk |
| Core dependency change | Branch by Abstraction | Type-safe, clear boundary |
| Critical business logic | Parallel Run | High confidence, validation |
| User-facing feature | Feature Flags | Gradual rollout, quick rollback |
| Database schema change | Database Migration | Zero downtime, backward compatible |
| Public API change | API Versioning | No breaking changes for clients |
| Library upgrade | Adapter Pattern | Bridge incompatible interfaces |

### Risk Assessment

**Low Risk Changes:**
- Adding new features (use Feature Flags)
- Refactoring internal code (use Branch by Abstraction)
- UI improvements (use Feature Flags)

**Medium Risk Changes:**
- Changing business logic (use Parallel Run)
- Database schema changes (use Database Migration)
- Replacing libraries (use Adapter Pattern)

**High Risk Changes:**
- Core system refactoring (use Strangler Fig)
- Authentication/authorization changes (use Parallel Run + Feature Flags)
- Data migration (use Database Migration + extensive testing)

---

## Best Practices Across All Strategies

### 1. Always Have Rollback Plan
```typescript
// Document rollback procedure
/*
 * ROLLBACK PROCEDURE:
 * 1. Set feature flag 'new-llm-provider' to false
 * 2. Restart application
 * 3. Monitor error rates
 * 4. If issues persist, revert commit abc123
 */
```

### 2. Monitor During Migration
```typescript
// Add metrics for both old and new
metrics.increment('llm.old.requests');
metrics.increment('llm.new.requests');
metrics.timing('llm.old.latency', duration);
metrics.timing('llm.new.latency', duration);
```

### 3. Test Both Paths
```typescript
describe('LLM Provider', () => {
  it('works with old implementation', async () => {
    featureFlags.disable('new-llm-provider');
    const result = await generateResponse('test');
    expect(result).toBeDefined();
  });

  it('works with new implementation', async () => {
    featureFlags.enable('new-llm-provider');
    const result = await generateResponse('test');
    expect(result).toBeDefined();
  });
});
```

### 4. Document Migration Status
```markdown
# Migration Status: LLM Provider Abstraction

**Status:** In Progress (Phase 2/4)
**Started:** 2026-01-15
**Target Completion:** 2026-02-28

## Progress
- [x] Phase 1: Create abstraction layer
- [x] Phase 2: Implement new providers
- [ ] Phase 3: Migrate existing code (60% complete)
- [ ] Phase 4: Remove old implementation

## Rollback
Feature flag: `new-llm-provider`
Current rollout: 50% of users
```

### 5. Communicate with Team
- Announce migration start
- Share migration plan
- Update documentation
- Provide examples
- Answer questions
- Celebrate completion

---

## Common Pitfalls

### Pitfall 1: Big Bang Migration
**Problem:** Trying to migrate everything at once
**Solution:** Use incremental strategies (Strangler Fig, Feature Flags)

### Pitfall 2: No Rollback Plan
**Problem:** Can't quickly revert if issues arise
**Solution:** Always have feature flags or version control rollback ready

### Pitfall 3: Insufficient Testing
**Problem:** New implementation breaks in production
**Solution:** Use Parallel Run to validate before switching

### Pitfall 4: Forgetting to Clean Up
**Problem:** Old code and flags remain forever
**Solution:** Schedule cleanup tasks, track technical debt

### Pitfall 5: Poor Communication
**Problem:** Team doesn't know about migration
**Solution:** Document, announce, and provide examples

---

## Migration Checklist

Before starting migration:
- [ ] Choose appropriate strategy
- [ ] Document migration plan
- [ ] Identify rollback procedure
- [ ] Add monitoring and metrics
- [ ] Write tests for both old and new
- [ ] Get team buy-in
- [ ] Schedule migration phases

During migration:
- [ ] Monitor error rates
- [ ] Compare old vs new performance
- [ ] Collect user feedback
- [ ] Document issues and solutions
- [ ] Update progress regularly

After migration:
- [ ] Remove old code
- [ ] Remove feature flags
- [ ] Update documentation
- [ ] Share lessons learned
- [ ] Celebrate success
