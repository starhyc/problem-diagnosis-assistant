from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import uuid
from datetime import datetime
import json
from langchain_core.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from app.core.llm_factory import llm_factory
from app.core.tool_registry import tool_registry
from app.core.logging_config import get_logger
from app.core.event_publisher import event_publisher
from app.services.modes.direct_executor import DirectExecutor
from app.services.modes.plan_execute_executor import PlanExecuteExecutor
from app.services.modes.react_executor import ReActExecutor
from app.services.modes.hierarchical_executor import HierarchicalExecutor

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
        default_mode: str = "plan_execute",
    ):
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.timeout = timeout
        self.llm: Optional[BaseChatModel] = None
        self.tools: List[BaseTool] = []
        self.retry_count = 3
        if not supported_modes:
            raise ValueError(f"{agent_name} must explicitly declare supported_modes")

        declared_modes = list(dict.fromkeys(supported_modes))
        unsupported_modes = [mode for mode in declared_modes if mode not in {"direct", "plan_execute", "react", "hierarchical"}]
        if unsupported_modes:
            raise ValueError(f"{agent_name} declares unsupported modes: {unsupported_modes}")
        if default_mode not in declared_modes:
            raise ValueError(f"{agent_name} default_mode={default_mode} must be included in supported_modes")

        self.supported_modes = declared_modes
        self.default_mode = default_mode
        self.mode_executors = {
            "direct": DirectExecutor(),
            "plan_execute": PlanExecuteExecutor(),
            "react": ReActExecutor(),
            "hierarchical": HierarchicalExecutor(),
        }

    @property
    def required_tool_name(self) -> Optional[str]:
        """Override in subclasses to enforce a mandatory tool call before LLM reasoning."""
        return None

    def build_required_tool_input(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses to define tool parameters."""
        return {}

    def _truncate_tool_result(self, payload: Any, max_length: int = 1200) -> Tuple[str, bool]:
        rendered = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        if len(rendered) <= max_length:
            return rendered, False
        return rendered[:max_length] + "...<truncated>", True

    async def run_required_tool(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mandatory tool and return a structured trace record."""
        tool_name = self.required_tool_name
        if not tool_name:
            return {}

        session_id = context.get("session_id", "unknown")
        trace_agent_id = context.get("trace_agent_id")
        trace_parent_id = context.get("trace_parent_id")
        tool_input = self.build_required_tool_input(task, context)
        started = asyncio.get_event_loop().time()
        success = False
        error = None
        raw_result: Any = ""
        tool = next((t for t in self.tools if getattr(t, "name", "") == tool_name), None)

        if not tool:
            error = f"required_tool_not_available:{tool_name}"
        else:
            try:
                raw_result = await asyncio.to_thread(tool.invoke, tool_input)
                success = True
            except Exception as exc:
                error = str(exc)

        duration_ms = int((asyncio.get_event_loop().time() - started) * 1000)
        truncated_result, truncated = self._truncate_tool_result(raw_result if success else error or "")
        record = {
            "tool": tool_name,
            "params": tool_input,
            "durationMs": duration_ms,
            "success": success,
            "error": error,
            "result": truncated_result,
            "truncated": truncated,
        }
        tool_registry.record_tool_execution(tool_name, self.agent_type, success, duration_ms)

        event_publisher.publish_diagnosis_event(session_id, {
            "type": "tool_call",
            "id": str(uuid.uuid4()),
            "agentId": trace_agent_id,
            "parentId": trace_parent_id,
            "agentName": self.agent_name,
            "toolCall": record,
            "timestamp": datetime.now().isoformat(),
        })
        return record

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
        requested_mode = mode or (context.get("mode") if context else None) or self.default_mode
        execution_mode = requested_mode
        mode_mismatch = None
        if execution_mode not in self.supported_modes:
            mismatch_reason = f"unsupported_mode_for_agent:{self.agent_name}"
            logger.warning(
                f"{self.agent_name} does not support mode={execution_mode}, "
                f"fallback to {self.default_mode}"
            )
            mode_mismatch = {
                "requested_mode": execution_mode,
                "fallback_mode": self.default_mode,
                "reason": mismatch_reason,
            }
            execution_mode = self.default_mode

        payload = context.copy() if context else {}
        payload["requested_mode"] = requested_mode
        payload["mode"] = execution_mode
        executor = self.mode_executors.get(execution_mode)
        if not executor:
            logger.warning(f"Unknown mode executor={execution_mode}, fallback to direct")
            mode_mismatch = {
                "requested_mode": execution_mode,
                "fallback_mode": "direct",
                "reason": f"executor_not_found:{execution_mode}",
            }
            execution_mode = "direct"
            executor = self.mode_executors["direct"]
        result = await executor.execute(self, task, payload)
        result.setdefault("effectiveMode", execution_mode)
        if mode_mismatch:
            result["modeMismatch"] = mode_mismatch
        return result

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
            "parentMode": context.get("parent_mode") if context else None,
            "forcedMode": context.get("forced_mode") if context else None,
            "fallbackMode": context.get("fallback_mode") if context else None,
            "mode": mode or (context.get("mode") if context else self.default_mode),
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
                    "parentMode": context.get("parent_mode") if context else None,
                    "forcedMode": context.get("forced_mode") if context else None,
                    "fallbackMode": context.get("fallback_mode") if context else None,
                    "mode": mode or (context.get("mode") if context else self.default_mode),
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
                mode_mismatch = result.get("modeMismatch")
                if mode_mismatch:
                    event_publisher.publish_diagnosis_event(session_id, {
                        "type": "mode_mismatch",
                        "id": str(uuid.uuid4()),
                        "agentId": trace_agent_id,
                        "parentId": trace_parent_id,
                        "agentName": self.agent_name,
                        "requestedMode": mode_mismatch.get("requested_mode"),
                        "fallbackMode": mode_mismatch.get("fallback_mode"),
                        "reason": mode_mismatch.get("reason"),
                        "timestamp": datetime.now().isoformat(),
                    })
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
                result.setdefault("traceAgentId", trace_agent_id)
                result.setdefault("parentId", trace_parent_id)
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
                        "traceAgentId": trace_agent_id,
                        "parentId": trace_parent_id,
                    }
                await asyncio.sleep(2 ** attempt)

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task"""
        raise NotImplementedError
