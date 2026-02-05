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

Current task: {task}
Context: {context}

Provide your metric analysis findings."""

class MetricAgent(BaseAgent):
    def __init__(self):
        super().__init__("metric", "Metric Analysis Agent")

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute metric analysis task"""
        if not self.llm:
            self.initialize()

        try:
            prompt = ChatPromptTemplate.from_template(METRIC_AGENT_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context))
            response = await self.llm.ainvoke(messages)

            return {
                "agent": self.agent_name,
                "result": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"MetricAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error"
            }
