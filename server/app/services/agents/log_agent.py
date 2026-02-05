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
        """Execute log analysis task"""
        if not self.llm:
            self.initialize()

        try:
            prompt = ChatPromptTemplate.from_template(LOG_AGENT_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context))
            response = await self.llm.ainvoke(messages)

            return {
                "agent": self.agent_name,
                "result": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"LogAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error"
            }
