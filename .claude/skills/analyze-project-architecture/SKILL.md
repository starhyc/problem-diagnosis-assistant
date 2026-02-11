---
name: analyze-project-architecture
description: This skill should be used when the user asks to "analyze project architecture", "study project B", "document architecture patterns", "analyze LLM implementation", "review real-time communication design", or wants to extract architectural insights from a reference codebase for learning purposes.
version: 0.1.0
---

# Project Architecture Analysis

## Purpose

Systematically analyze a target project's architecture, design patterns, and implementation details to produce comprehensive, structured documentation. Focus on extracting reusable patterns, architectural decisions, and best practices that can inform improvements to other projects.

## When to Use This Skill

Use this skill when:
- Analyzing a reference project (Project B) to learn from its architecture
- Documenting architectural patterns for knowledge transfer
- Studying LLM integration patterns and real-time communication designs
- Extracting best practices from production codebases
- Creating architectural reference documentation for team learning

## Analysis Workflow

### Phase 1: Initial Discovery

**Explore project structure:**
1. Identify the project type (frontend, backend, full-stack)
2. Map directory structure and key modules
3. Locate configuration files (package.json, requirements.txt, docker-compose.yml)
4. Identify technology stack and frameworks

**Use the Explore agent for broad discovery:**
```
Task tool with subagent_type=Explore
Prompt: "Map the overall architecture of this project, identify main modules and their responsibilities"
```

### Phase 2: Deep Dive Analysis

**For each architectural domain, analyze:**

#### LLM Architecture
- Provider abstraction patterns (multi-provider support, fallback chains)
- Token management and cost tracking
- Streaming response handling
- Prompt engineering patterns
- Context window management
- Error handling and retry logic

#### Real-Time Communication
- WebSocket implementation patterns
- Message protocol design
- Connection lifecycle management
- Reconnection strategies
- State synchronization mechanisms
- Pub/Sub patterns (Redis, message queues)

#### State Management
- State store architecture (Zustand, Redux, Context)
- State persistence strategies
- Event sourcing patterns
- Optimistic updates
- State recovery mechanisms

#### Code Organization
- Module boundaries and separation of concerns
- Dependency injection patterns
- Service layer architecture
- API client design
- Type system usage

#### Infrastructure Patterns
- Database schema design
- Caching strategies
- Background job processing (Celery, Bull)
- Deployment architecture
- Monitoring and observability

### Phase 3: Documentation Output

**Create structured analysis documents:**

1. **architecture-overview.md** - High-level system architecture
   - System diagram (textual description)
   - Component responsibilities
   - Data flow patterns
   - Technology stack rationale

2. **llm-integration-patterns.md** - LLM implementation details
   - Provider abstraction design
   - Streaming and token management
   - Prompt templates and strategies
   - Error handling patterns

3. **realtime-communication.md** - Real-time features analysis
   - WebSocket architecture
   - Message protocol specification
   - State synchronization approach
   - Scalability considerations

4. **state-management.md** - State handling patterns
   - Store architecture
   - State persistence strategy
   - Event sourcing implementation
   - Recovery mechanisms

5. **best-practices.md** - Extracted best practices
   - Code organization principles
   - Error handling patterns
   - Testing strategies
   - Security considerations

### Phase 4: Pattern Extraction

**Identify reusable patterns:**
- Abstract implementation details into pattern descriptions
- Document trade-offs and design decisions
- Note dependencies and prerequisites
- Highlight potential pitfalls

**Create pattern catalog:**
```markdown
## Pattern: Multi-Provider LLM Abstraction

**Problem:** Need to support multiple LLM providers with fallback

**Solution:** Factory pattern with provider interface

**Implementation:**
- Abstract LLM interface
- Provider-specific implementations
- Fallback chain with retry logic

**Trade-offs:**
- Pros: Flexibility, resilience
- Cons: Additional abstraction layer

**Prerequisites:**
- Async/await support
- Error handling framework
```

## Analysis Techniques

### Code Reading Strategy

**Start broad, then narrow:**
1. Read entry points (main.py, App.tsx, index.ts)
2. Follow imports to understand module structure
3. Identify core abstractions and interfaces
4. Deep dive into implementation details

**Use specialized tools:**
- `Grep` for finding patterns across codebase
- `Read` for examining specific files
- `Glob` for discovering file patterns
- `Task` with Explore agent for broad questions

### Documentation Standards

**Be specific and actionable:**
- Include file paths and line numbers
- Show actual code snippets (not pseudocode)
- Document "why" not just "what"
- Note version-specific details

**Structure for clarity:**
- Use clear headings and sections
- Include table of contents for long documents
- Add cross-references between related sections
- Provide examples for complex patterns

### Critical Analysis

**Evaluate design decisions:**
- Identify strengths and weaknesses
- Note scalability considerations
- Document security implications
- Consider maintainability trade-offs

**Question assumptions:**
- Why this pattern over alternatives?
- What problems does this solve?
- What new problems does it introduce?
- How does it scale?

## Output Organization

**Create analysis directory structure:**
```
project-b-analysis/
├── architecture-overview.md
├── llm-integration-patterns.md
├── realtime-communication.md
├── state-management.md
├── best-practices.md
├── code-snippets/
│   ├── llm-factory.ts
│   ├── websocket-manager.ts
│   └── state-store.ts
└── diagrams/
    ├── system-architecture.md
    └── data-flow.md
```

## Tips for Effective Analysis

**Focus on transferable knowledge:**
- Extract patterns, not just code
- Document rationale behind decisions
- Identify prerequisites for adoption
- Note context-specific considerations

**Maintain objectivity:**
- Document both strengths and weaknesses
- Avoid cargo-culting (copying without understanding)
- Consider alternative approaches
- Note when patterns may not apply elsewhere

**Be thorough but concise:**
- Cover all major architectural domains
- Avoid excessive detail on trivial aspects
- Focus on novel or exemplary patterns
- Summarize common patterns briefly

## Additional Resources

### Reference Files

For detailed analysis templates and checklists:
- **`references/analysis-templates.md`** - Structured templates for each analysis domain
- **`references/pattern-catalog.md`** - Common architectural patterns to look for

### Examples

Working examples in `examples/`:
- **`example-analysis-output/`** - Sample analysis documentation structure

## Common Pitfalls to Avoid

- **Surface-level analysis:** Don't just list technologies; understand how and why they're used
- **Missing context:** Document the problems being solved, not just solutions
- **Over-generalization:** Note when patterns are context-specific
- **Incomplete coverage:** Ensure all major architectural domains are analyzed
- **Copy-paste mentality:** Focus on understanding, not just documenting code

## Success Criteria

Analysis is complete when:
- All major architectural domains are documented
- Key patterns are extracted and explained
- Design trade-offs are clearly articulated
- Documentation is actionable for improvement efforts
- Code examples support pattern descriptions
- Cross-references connect related concepts
