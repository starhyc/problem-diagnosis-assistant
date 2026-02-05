# Workflow Customization

## Overview

The system supports two workflow modes: Simple (centralized) and Complex (LangGraph DAG).

## Simple Workflow

Sequential execution coordinated by CoordinatorAgent:

```python
async def simple_flow(state: DiagnosisState) -> DiagnosisState:
    result = await coordinator.execute_with_timeout(
        state["symptom"],
        {"phase": "analysis"}
    )
    state["messages"].append(result)
    return state
```

**Use when:**
- Quick diagnosis needed
- Single symptom analysis
- Limited agent collaboration required

## Complex Workflow

LangGraph-based DAG with parallel execution:

```python
workflow = StateGraph(DiagnosisState)
workflow.add_node("coordinator_init", coordinator_init)
workflow.add_node("parallel_analysis", parallel_analysis)
workflow.add_conditional_edges("synthesis", should_query_knowledge, {
    "yes": "knowledge_match",
    "no": "final_decision"
})
```

**Use when:**
- Multi-faceted problems
- Parallel agent execution needed
- Conditional logic required

## Creating Custom Workflows

### 1. Define State

```python
class CustomState(TypedDict):
    symptom: str
    custom_field: str
    # Add your fields
```

### 2. Create Workflow Nodes

```python
async def custom_node(state: CustomState) -> CustomState:
    # Node logic
    event_publisher.publish_diagnosis_event(session_id, {
        "type": "workflow_node_entered",
        "node_name": "custom_node"
    })

    result = await agent.execute_with_timeout(task, context)
    state["custom_field"] = result

    return state
```

### 3. Build Graph

```python
workflow = StateGraph(CustomState)
workflow.add_node("node1", custom_node)
workflow.add_edge("node1", "node2")
workflow.set_entry_point("node1")
compiled = workflow.compile()
```

### 4. Execute

```python
result = await compiled.ainvoke(initial_state)
```

## Conditional Routing

```python
def should_escalate(state: DiagnosisState) -> str:
    return "escalate" if state["confidence"] < 50 else "complete"

workflow.add_conditional_edges("analysis", should_escalate, {
    "escalate": "deep_analysis",
    "complete": END
})
```

## Parallel Execution

```python
async def parallel_analysis(state: DiagnosisState) -> DiagnosisState:
    import asyncio

    results = await asyncio.gather(
        log_agent.execute_with_timeout(symptom, context),
        metric_agent.execute_with_timeout(symptom, context)
    )

    state["messages"].extend(results)
    return state
```

## Workflow Control

### Pause/Resume

```python
workflow_engine.pause_workflow(session_id)
workflow_engine.resume_workflow(session_id)
```

### Cancel

```python
workflow_engine.cancel_workflow(session_id)
```

## Best Practices

1. **Event publication**: Publish events at node entry/exit
2. **State snapshots**: Save state after major nodes
3. **Error handling**: Wrap agent calls in try/except
4. **Timeout management**: Set appropriate timeouts per node
5. **Conditional logic**: Use confidence scores for routing
