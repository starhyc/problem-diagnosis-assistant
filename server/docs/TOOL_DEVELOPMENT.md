# Tool Development Guide

## Overview

Tools extend agent capabilities by providing access to external systems (ELK, Git, databases, APIs).

## Creating a New Tool

### 1. Define Tool Class

```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class MyToolInput(BaseModel):
    param1: str = Field(description="Parameter description")
    param2: int = Field(default=10, description="Optional parameter")

class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "What this tool does"
    args_schema: Type[BaseModel] = MyToolInput

    def _run(self, param1: str, param2: int = 10) -> str:
        # Implementation
        return f"Result: {param1}"
```

### 2. Register Tool

Add to `app/tools/base_tools.py` or create new file:

```python
from app.core.tool_registry import tool_registry

tool_registry.register_tool("my_tool", MyTool())
```

### 3. Assign to Agents

Update `app/core/tool_registry.py`:

```python
self._agent_tool_map = {
    "log": ["elk_query", "my_tool"],
    "code": ["git_search"],
    # ...
}
```

## Example: ELK Query Tool

```python
class ELKQueryTool(BaseTool):
    name: str = "elk_query"
    description: str = "Query ELK logs for error patterns"
    args_schema: Type[BaseModel] = ELKQueryInput

    def _run(self, query: str, index: str = "logs-*", size: int = 100) -> str:
        from elasticsearch import Elasticsearch
        es = Elasticsearch(['http://localhost:9200'])

        result = es.search(index=index, body={
            "query": {"query_string": {"query": query}},
            "size": size
        })

        return str(result['hits']['hits'])
```

## Best Practices

1. **Clear descriptions**: Help LLM understand when to use the tool
2. **Typed inputs**: Use Pydantic models for validation
3. **Error handling**: Return error messages, don't raise exceptions
4. **Concise output**: Return structured data, not verbose text
5. **Idempotent**: Tools should be safe to retry

## Tool Execution Monitoring

Tool usage is automatically logged:

```python
tool_registry.record_tool_execution(
    tool_name="elk_query",
    agent_type="log",
    success=True,
    duration_ms=150.5
)
```

## Testing Tools

```python
def test_my_tool():
    tool = MyTool()
    result = tool._run(param1="test")
    assert "Result: test" in result
```
