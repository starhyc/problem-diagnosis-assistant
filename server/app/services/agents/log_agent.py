from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.services.agents.base_agent import BaseAgent
from app.core.logging_config import get_logger

logger = get_logger(__name__)

LOG_AGENT_PROMPT = """You are a Log Analysis Agent specialized in analyzing system logs.

Your role:
- Parse and analyze log files from various sources (ELK, application logs, system logs)
- Identify error patterns, anomalies, and suspicious activities
- Extract relevant timestamps, error codes, and stack traces
- Correlate log entries to identify root causes

Current task: {task}
Context: {context}

Provide your log analysis findings."""


class LogAgent(BaseAgent):
    def __init__(self):
        super().__init__("log", "Log Analysis Agent")

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.llm:
            self.initialize()

        try:
            prompt = ChatPromptTemplate.from_template(LOG_AGENT_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context))
            response = await self.llm.ainvoke(messages)
            usage = self._extract_usage(response)
            return {
                "agent": self.agent_name,
                "result": response.content,
                "status": "success",
                "model": self._extract_model_name(),
                **usage,
                "costEstimate": self._estimate_cost(usage["inputTokens"], usage["outputTokens"]),
            }
        except Exception as e:
            logger.error(f"LogAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error",
                "model": self._extract_model_name(),
                "inputTokens": 0,
                "outputTokens": 0,
                "costEstimate": 0,
            }
