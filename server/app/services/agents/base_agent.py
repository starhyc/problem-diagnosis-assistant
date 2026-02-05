from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from app.core.llm_factory import llm_factory
from app.core.tool_registry import tool_registry
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class AgentTimeoutError(Exception):
    """Raised when agent execution times out"""
    pass

class BaseAgent(ABC):
    def __init__(self, agent_type: str, agent_name: str, timeout: int = 300):
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.timeout = timeout
        self.llm: Optional[BaseChatModel] = None
        self.tools: List[BaseTool] = []
        self.retry_count = 3

    def initialize(self):
        """Initialize agent with LLM and tools"""
        try:
            self.llm = llm_factory.create_with_fallback()
            self.tools = tool_registry.get_tools_for_agent(self.agent_type)
            logger.info(f"Agent initialized: {self.agent_name} with {len(self.tools)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_name}: {e}")
            raise

    async def execute_with_timeout(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task with timeout and retry logic"""
        for attempt in range(self.retry_count):
            try:
                result = await asyncio.wait_for(
                    self.execute(task, context),
                    timeout=self.timeout
                )
                return result
            except asyncio.TimeoutError:
                logger.warning(f"{self.agent_name} timeout on attempt {attempt + 1}/{self.retry_count}")
                if attempt == self.retry_count - 1:
                    raise AgentTimeoutError(f"{self.agent_name} exceeded timeout of {self.timeout}s")
            except Exception as e:
                logger.error(f"{self.agent_name} error on attempt {attempt + 1}/{self.retry_count}: {e}")
                if attempt == self.retry_count - 1:
                    return {
                        "agent": self.agent_name,
                        "result": f"Failed after {self.retry_count} attempts: {str(e)}",
                        "status": "error"
                    }
                await asyncio.sleep(2 ** attempt)

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task"""
        pass
