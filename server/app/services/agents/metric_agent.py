from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from app.services.agents.base_agent import BaseAgent
from app.core.logging_config import get_logger
from app.schemas.events import AgentFailureExplanation

logger = get_logger(__name__)

METRIC_AGENT_PROMPT = """You are a Metric Analysis Agent specialized in analyzing monitoring data and system metrics.

Your role:
- Analyze metrics from monitoring systems (Prometheus, Grafana, CloudWatch, etc.)
- Identify performance anomalies, resource bottlenecks, and trends
- Correlate metrics with incidents and symptoms
- Provide data-driven insights on system health

You MUST ground every conclusion in tool evidence.
- If evidence is insufficient, explicitly output "INSUFFICIENT_EVIDENCE" and list missing evidence.
- Do NOT fabricate facts beyond the tool output.

Current task: {task}
Context: {context}
Tool evidence (mandatory metric/log query): {tool_evidence}

Provide your metric analysis findings."""


class MetricAgent(BaseAgent):
    def __init__(self):
        super().__init__("metric", "Metric Analysis Agent", supported_modes=["plan_execute", "react", "hierarchical"], default_mode="plan_execute")

    @property
    def required_tool_name(self) -> str:
        return "elk_query"

    def build_required_tool_input(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        symptom = context.get("symptom") or task
        return {"query": symptom, "index": "metrics-*", "size": 50}

    def _failure_explanation(self, tool_record: Dict[str, Any], content: str) -> Dict[str, Any]:
        missing: List[str] = []
        status = "ok"
        reason = None
        if tool_record and not tool_record.get("success", False):
            status = "insufficient_evidence"
            reason = "tool_query_failed"
            missing.append("指标查询结果")
        if "INSUFFICIENT_EVIDENCE" in (content or ""):
            status = "insufficient_evidence"
            reason = reason or "agent_marked_insufficient"
            missing.append("时间窗口或关键指标标签")
        return AgentFailureExplanation(status=status, reason=reason, missing_evidence=missing).model_dump()

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.llm:
            self.initialize()

        try:
            tool_record = await self.run_required_tool(task, context)
            prompt = ChatPromptTemplate.from_template(METRIC_AGENT_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context), tool_evidence=str(tool_record))
            response = await self.llm.ainvoke(messages)
            usage = self._extract_usage(response)
            content = str(response.content)
            return {
                "agent": self.agent_name,
                "result": content,
                "status": "success",
                "failure_explanation": self._failure_explanation(tool_record, content),
                "model": self._extract_model_name(),
                "toolCalls": [tool_record] if tool_record else [],
                **usage,
                "costEstimate": self._estimate_cost(usage["inputTokens"], usage["outputTokens"]),
            }
        except Exception as e:
            logger.error(f"MetricAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error",
                "failure_explanation": AgentFailureExplanation(status="error", reason=str(e), missing_evidence=["指标证据"]).model_dump(),
                "model": self._extract_model_name(),
                "inputTokens": 0,
                "outputTokens": 0,
                "costEstimate": 0,
            }
