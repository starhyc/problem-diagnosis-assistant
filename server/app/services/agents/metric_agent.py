from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.services.agents.base_agent import BaseAgent
from app.core.logging_config import get_logger

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
        super().__init__("metric", "Metric Analysis Agent")

    @property
    def required_tool_name(self) -> str:
        return "elk_query"

    def build_required_tool_input(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        symptom = context.get("symptom") or task
        return {"query": symptom, "index": "metrics-*", "size": 50}

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.llm:
            self.initialize()

        try:
            tool_record = await self.run_required_tool(task, context)
            prompt = ChatPromptTemplate.from_template(METRIC_AGENT_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context), tool_evidence=str(tool_record))
            response = await self.llm.ainvoke(messages)
            usage = self._extract_usage(response)
            return {
                "agent": self.agent_name,
                "result": response.content,
                "status": "success",
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
                "model": self._extract_model_name(),
                "inputTokens": 0,
                "outputTokens": 0,
                "costEstimate": 0,
            }
