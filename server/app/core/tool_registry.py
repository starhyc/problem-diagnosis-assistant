from typing import Dict, List, Optional
from langchain_core.tools import BaseTool
from app.core.logging_config import get_logger
from functools import lru_cache

logger = get_logger(__name__)

class ToolRegistry:
    _instance: Optional['ToolRegistry'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._agent_tool_map = {
                "coordinator": [],
                "log": ["elk_query"],
                "code": ["git_search"],
                "knowledge": ["db_query"],
                "metric": ["elk_query", "db_query"]
            }
            cls._instance._register_defaults()
        return cls._instance

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
        logger.info(f"Agent '{agent_type}' configured with tools: {tool_names}")

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())

tool_registry = ToolRegistry()
