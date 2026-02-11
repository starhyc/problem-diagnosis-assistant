import json
from functools import lru_cache
from typing import Dict, List, Optional

from langchain_core.tools import BaseTool

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging_config import get_logger
from app.models.case import Setting

logger = get_logger(__name__)

DEFAULT_AGENT_TOOL_MAP = {
    "coordinator": ["db_query"],
    "log": ["elk_query"],
    "code": ["git_search"],
    "knowledge": ["db_query"],
    "metric": ["elk_query", "db_query"],
}


class ToolRegistry:
    _instance: Optional["ToolRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._agent_tool_map = cls._instance._load_agent_tool_map()
            cls._instance._register_defaults()
        return cls._instance

    def _load_agent_tool_map(self) -> Dict[str, List[str]]:
        """Load agent->tool mapping from DB setting first, then settings env, then defaults."""
        # 1) DB setting source
        try:
            with SessionLocal() as db:
                row = (
                    db.query(Setting)
                    .filter(Setting.setting_type == "agent_tool_map", Setting.setting_id == "default")
                    .first()
                )
                if row and row.config:
                    payload = json.loads(row.config)
                    if isinstance(payload, dict):
                        logger.info("Loaded agent tool map from database setting")
                        return {k: list(v) for k, v in payload.items() if isinstance(v, list)}
        except Exception as exc:
            logger.warning(f"Failed loading agent tool map from DB: {exc}")

        # 2) settings source
        raw_map = getattr(settings, "agent_tool_map", None)
        if raw_map and isinstance(raw_map, str):
            try:
                payload = json.loads(raw_map)
                if isinstance(payload, dict):
                    logger.info("Loaded agent tool map from settings.agent_tool_map")
                    return {k: list(v) for k, v in payload.items() if isinstance(v, list)}
            except Exception as exc:
                logger.warning(f"Invalid settings.agent_tool_map JSON, fallback to default: {exc}")

        return dict(DEFAULT_AGENT_TOOL_MAP)

    def _register_defaults(self):
        """Register default tools"""
        try:
            from app.tools.base_tools import ELKQueryTool, GitSearchTool, DBQueryTool

            self.register_tool("elk_query", ELKQueryTool())
            self.register_tool("git_search", GitSearchTool())
            self.register_tool("db_query", DBQueryTool())
        except Exception as e:
            logger.error(f"Failed to register default tools: {e}")

    def register_tool(self, name: str, tool: BaseTool, config: Optional[Dict] = None):
        """Register a tool with optional configuration"""
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already registered")

        self._tools[name] = tool
        logger.info(f"Tool registered: {name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)

    @lru_cache(maxsize=128)
    def get_tools_for_agent(self, agent_type: str) -> List[BaseTool]:
        """Get all tools configured for an agent type"""
        tool_names = self._agent_tool_map.get(agent_type, [])
        tools = [self._tools[name] for name in tool_names if name in self._tools]
        logger.info(f"Retrieved {len(tools)} tools for agent: {agent_type}")
        return tools

    def record_tool_execution(self, tool_name: str, agent_type: str, success: bool, duration_ms: float):
        """Record tool execution metrics"""
        logger.info(f"Tool execution: {tool_name} by {agent_type}, success={success}, duration={duration_ms}ms")

    def set_agent_tools(self, agent_type: str, tool_names: List[str]):
        """Configure which tools an agent can use"""
        self._agent_tool_map[agent_type] = tool_names
        self.get_tools_for_agent.cache_clear()
        logger.info(f"Agent '{agent_type}' configured with tools: {tool_names}")

    def reload_agent_tool_map(self):
        self._agent_tool_map = self._load_agent_tool_map()
        self.get_tools_for_agent.cache_clear()

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())


tool_registry = ToolRegistry()
