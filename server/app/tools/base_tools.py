from langchain_core.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field


class ELKQueryInput(BaseModel):
    query: str = Field(description="Elasticsearch query string")
    index: str = Field(default="logs-*", description="Index pattern")
    size: int = Field(default=100, description="Number of results")


class ELKQueryTool(BaseTool):
    name: str = "elk_query"
    description: str = "Query ELK logs for error patterns and anomalies"
    args_schema: Type[BaseModel] = ELKQueryInput

    def _run(self, query: str, index: str = "logs-*", size: int = 100) -> str:
        # Mock implementation - replace with actual ELK client
        return f"Mock ELK results for query: {query} in {index}"


class GitSearchInput(BaseModel):
    pattern: str = Field(description="Code pattern to search")
    file_pattern: str = Field(default="**/*.py", description="File glob pattern")


class GitSearchTool(BaseTool):
    name: str = "git_search"
    description: str = "Search code repository for patterns and recent changes"
    args_schema: Type[BaseModel] = GitSearchInput

    def _run(self, pattern: str, file_pattern: str = "**/*.py") -> str:
        # Mock implementation - replace with actual git grep
        return f"Mock git search results for: {pattern} in {file_pattern}"


class DBQueryInput(BaseModel):
    query: str = Field(description="SQL query to execute")
    database: str = Field(default="main", description="Database name")


class DBQueryTool(BaseTool):
    name: str = "db_query"
    description: str = "Query database for configuration and state information"
    args_schema: Type[BaseModel] = DBQueryInput

    def _run(self, query: str, database: str = "main") -> str:
        # Mock implementation - replace with actual DB client
        return f"Mock DB results for: {query} on {database}"
