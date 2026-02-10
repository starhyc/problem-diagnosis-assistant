from __future__ import annotations

import fnmatch
import json
import sqlite3
import subprocess
from hashlib import sha256
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Type

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


_WRITE_IDEMPOTENCY_CACHE: Dict[str, bool] = {}


def _is_write_query(query: str) -> bool:
    head = query.strip().split(maxsplit=1)
    if not head:
        return False
    return head[0].upper() in {"INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER"}


def _build_idempotency_key(session_id: str, action_id: str, step_id: str) -> str:
    raw = f"{session_id}:{action_id}:{step_id}"
    return sha256(raw.encode("utf-8")).hexdigest()


class ToolAdapter(ABC):
    """统一工具适配层接口，屏蔽具体实现差异。"""

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        raise NotImplementedError


class ELKHttpAdapter(ToolAdapter):
    def __init__(self, base_url: Optional[str] = None, timeout: int = 5) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def execute(self, **kwargs: Any) -> str:
        query = kwargs["query"]
        index = kwargs.get("index", "logs-*")
        size = kwargs.get("size", 100)

        if not self.base_url:
            return "ELK endpoint not configured; set ELK_URL to enable live queries."

        endpoint = self.base_url.rstrip("/") + f"/{index}/_search"
        payload = {
            "size": size,
            "query": {
                "query_string": {
                    "query": query,
                }
            },
        }

        response = requests.post(endpoint, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        return json.dumps(
            {
                "total": data.get("hits", {}).get("total", {}),
                "hits": [h.get("_source", {}) for h in hits],
            },
            ensure_ascii=False,
        )


class GitSearchAdapter(ToolAdapter):
    def __init__(self, repo_path: Optional[Path] = None) -> None:
        self.repo_path = repo_path or Path.cwd()

    def execute(self, **kwargs: Any) -> str:
        pattern = kwargs["pattern"]
        file_pattern = kwargs.get("file_pattern", "**/*.py")

        cmd = ["git", "grep", "-n", pattern]
        result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr.strip() or "git grep failed")

        if result.returncode == 1 or not result.stdout.strip():
            return "No matches found"

        filtered = []
        for line in result.stdout.splitlines():
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue
            file_path = parts[0]
            if fnmatch.fnmatch(file_path, file_pattern) or file_pattern in ("*", "**/*"):
                filtered.append(line)

        return "\n".join(filtered[:200]) if filtered else "No matches found"


class SQLiteAdapter(ToolAdapter):
    def __init__(self, database_url: str) -> None:
        if not database_url.startswith("sqlite"):
            raise ValueError("SQLiteAdapter only supports sqlite URLs")
        self.database_path = database_url.replace("sqlite:///", "")

    def execute(self, **kwargs: Any) -> str:
        query = kwargs["query"]
        limit = kwargs.get("limit", 100)
        wrapped = query.strip().rstrip(";")
        session_id = kwargs.get("session_id", "unknown")
        action_id = kwargs.get("action_id", "db_query")
        step_id = kwargs.get("step_id", "default")
        idempotency_key = kwargs.get("idempotency_key") or _build_idempotency_key(session_id, action_id, step_id)

        if _is_write_query(wrapped):
            if idempotency_key in _WRITE_IDEMPOTENCY_CACHE:
                return json.dumps({"status": "duplicate", "idempotency_key": idempotency_key}, ensure_ascii=False)
            _WRITE_IDEMPOTENCY_CACHE[idempotency_key] = True

            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(wrapped)
                conn.commit()
                return json.dumps({"status": "ok", "rows_affected": cursor.rowcount, "idempotency_key": idempotency_key}, ensure_ascii=False)

        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"SELECT * FROM ({wrapped}) LIMIT ?", (limit,))
            rows = [dict(r) for r in cursor.fetchall()]

        return json.dumps(rows, ensure_ascii=False)


class ELKQueryInput(BaseModel):
    query: str = Field(description="Elasticsearch query string")
    index: str = Field(default="logs-*", description="Index pattern")
    size: int = Field(default=100, description="Number of results")


class ELKQueryTool(BaseTool):
    name: str = "elk_query"
    description: str = "Query ELK logs for error patterns and anomalies"
    args_schema: Type[BaseModel] = ELKQueryInput

    def __init__(self, adapter: Optional[ToolAdapter] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self._adapter = adapter or ELKHttpAdapter()

    def _run(self, query: str, index: str = "logs-*", size: int = 100) -> str:
        return self._adapter.execute(query=query, index=index, size=size)


class GitSearchInput(BaseModel):
    pattern: str = Field(description="Code pattern to search")
    file_pattern: str = Field(default="**/*.py", description="File glob pattern")


class GitSearchTool(BaseTool):
    name: str = "git_search"
    description: str = "Search code repository for patterns and recent changes"
    args_schema: Type[BaseModel] = GitSearchInput

    def __init__(self, adapter: Optional[ToolAdapter] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self._adapter = adapter or GitSearchAdapter()

    def _run(self, pattern: str, file_pattern: str = "**/*.py") -> str:
        return self._adapter.execute(pattern=pattern, file_pattern=file_pattern)


class DBQueryInput(BaseModel):
    query: str = Field(description="SQL query to execute")
    limit: int = Field(default=100, description="Max rows returned")
    session_id: str = Field(default="unknown", description="Workflow session ID")
    action_id: str = Field(default="db_query", description="Action identifier")
    step_id: str = Field(default="default", description="Step identifier")
    idempotency_key: Optional[str] = Field(default=None, description="Deduplication key for write operations")


class DBQueryTool(BaseTool):
    name: str = "db_query"
    description: str = "Query database for configuration and state information"
    args_schema: Type[BaseModel] = DBQueryInput

    def __init__(self, adapter: Optional[ToolAdapter] = None, **kwargs: Any):
        super().__init__(**kwargs)
        if adapter is None:
            from app.core.config import settings

            adapter = SQLiteAdapter(settings.database_url)
        self._adapter = adapter

    def _run(
        self,
        query: str,
        limit: int = 100,
        session_id: str = "unknown",
        action_id: str = "db_query",
        step_id: str = "default",
        idempotency_key: Optional[str] = None,
    ) -> str:
        return self._adapter.execute(
            query=query,
            limit=limit,
            session_id=session_id,
            action_id=action_id,
            step_id=step_id,
            idempotency_key=idempotency_key,
        )
