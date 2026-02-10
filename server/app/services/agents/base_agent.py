from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
import uuid
from datetime import datetime
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from app.core.llm_factory import llm_factory
from app.core.tool_registry import tool_registry
from app.core.logging_config import get_logger
from app.core.event_publisher import event_publisher

logger = get_logger(__name__)


class AgentTimeoutError(Exception):
    """Raised when agent execution times out"""


class BaseAgent(ABC):
    def __init__(
        self,
        agent_type: str,
        agent_name: str,
        timeout: int = 300,
        supported_modes: Optional[List[str]] = None,
        default_mode: str = "prd_standard",
    ):
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.timeout = timeout
        self.llm: Optional[BaseChatModel] = None
        self.tools: List[BaseTool] = []
        self.retry_count = 3
        self.supported_modes = supported_modes or [default_mode]
        self.default_mode = default_mode

    def _extract_model_name(self) -> str:
        return getattr(self.llm, "model_name", "unknown") if self.llm else "unknown"

    def _extract_usage(self, response: Any) -> Dict[str, int]:
        usage = getattr(response, "usage_metadata", None) or {}
        input_tokens = int(usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or usage.get("completion_tokens", 0) or 0)
        return {
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
        }

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # conservative placeholder estimate until provider billing table is wired.
        return round((input_tokens * 0.0000015) + (output_tokens * 0.000002), 6)

    def initialize(self):
        """Initialize agent with LLM and tools"""
        try:
            self.llm = llm_factory.create_with_fallback()
            self.tools = tool_registry.get_tools_for_agent(self.agent_type)
            logger.info(f"Agent initialized: {self.agent_name} with {len(self.tools)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_name}: {e}")
            raise

    async def run(self, task: str, mode: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Unified agent runtime interface."""
        execution_mode = mode or self.default_mode
        if execution_mode not in self.supported_modes:
            logger.warning(
                f"{self.agent_name} does not support mode={execution_mode}, "
                f"fallback to {self.default_mode}"
            )
            execution_mode = self.default_mode

        payload = context.copy() if context else {}
        payload["mode"] = execution_mode
        return await self.execute(task, payload)

    async def execute_with_timeout(self, task: str, context: Dict[str, Any], mode: Optional[str] = None) -> Dict[str, Any]:
        """Execute agent task with timeout and retry logic"""
        session_id = context.get("session_id", "unknown")
        trace_parent_id = context.get("trace_parent_id")
        trace_agent_id = context.get("trace_agent_id") or str(uuid.uuid4())
        started_at = asyncio.get_event_loop().time()
        event_publisher.publish_diagnosis_event(session_id, {
            "type": "agent_trace_start",
            "agentId": trace_agent_id,
            "agentName": self.agent_name,
            "parentId": trace_parent_id,
            "toolCall": None,
            "latency": 0,
            "inputTokens": 0,
            "outputTokens": 0,
            "model": self._extract_model_name(),
            "costEstimate": 0,
            "startTime": datetime.now().isoformat(),
            "taskDescription": task,
        })

        for attempt in range(self.retry_count):
            try:
                event_publisher.publish_diagnosis_event(session_id, {
                    "type": "agent_trace_step",
                    "agentId": trace_agent_id,
                    "parentId": trace_parent_id,
                    "id": str(uuid.uuid4()),
                    "stepType": "llm_thinking",
                    "content": f"attempt={attempt + 1}",
                    "toolCall": None,
                    "latency": 0,
                    "inputTokens": 0,
                    "outputTokens": 0,
                    "model": self._extract_model_name(),
                    "costEstimate": 0,
                    "timestamp": datetime.now().isoformat(),
                })
                result = await asyncio.wait_for(
                    self.run(task, mode=mode, context=context),
                    timeout=self.timeout,
                )
                latency = int((asyncio.get_event_loop().time() - started_at) * 1000)
                input_tokens = int(result.get("inputTokens", 0))
                output_tokens = int(result.get("outputTokens", 0))
                event_publisher.publish_diagnosis_event(session_id, {
                    "type": "agent_trace_complete",
                    "agentId": trace_agent_id,
                    "parentId": trace_parent_id,
                    "status": result.get("status", "success"),
                    "endTime": datetime.now().isoformat(),
                    "latency": latency,
                    "duration": latency,
                    "toolCall": None,
                    "inputTokens": input_tokens,
                    "outputTokens": output_tokens,
                    "totalTokens": {"input": input_tokens, "output": output_tokens},
                    "model": result.get("model", self._extract_model_name()),
                    "costEstimate": result.get("costEstimate", self._estimate_cost(input_tokens, output_tokens)),
                })
                return result
            except asyncio.TimeoutError:
                logger.warning(f"{self.agent_name} timeout on attempt {attempt + 1}/{self.retry_count}")
                if attempt == self.retry_count - 1:
                    latency = int((asyncio.get_event_loop().time() - started_at) * 1000)
                    event_publisher.publish_diagnosis_event(session_id, {
                        "type": "agent_trace_complete",
                        "agentId": trace_agent_id,
                        "parentId": trace_parent_id,
                        "status": "failed",
                        "error": f"timeout_{self.timeout}s",
                        "latency": latency,
                        "duration": latency,
                        "toolCall": None,
                        "inputTokens": 0,
                        "outputTokens": 0,
                        "totalTokens": {"input": 0, "output": 0},
                        "model": self._extract_model_name(),
                        "costEstimate": 0,
                    })
                    raise AgentTimeoutError(f"{self.agent_name} exceeded timeout of {self.timeout}s")
            except Exception as e:
                logger.error(f"{self.agent_name} error on attempt {attempt + 1}/{self.retry_count}: {e}")
                if attempt == self.retry_count - 1:
                    latency = int((asyncio.get_event_loop().time() - started_at) * 1000)
                    event_publisher.publish_diagnosis_event(session_id, {
                        "type": "agent_trace_complete",
                        "agentId": trace_agent_id,
                        "parentId": trace_parent_id,
                        "status": "failed",
                        "error": str(e),
                        "latency": latency,
                        "duration": latency,
                        "toolCall": None,
                        "inputTokens": 0,
                        "outputTokens": 0,
                        "totalTokens": {"input": 0, "output": 0},
                        "model": self._extract_model_name(),
                        "costEstimate": 0,
                    })
                    return {
                        "agent": self.agent_name,
                        "result": f"Failed after {self.retry_count} attempts: {str(e)}",
                        "status": "error",
                    }
                await asyncio.sleep(2 ** attempt)

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task"""
        raise NotImplementedError
