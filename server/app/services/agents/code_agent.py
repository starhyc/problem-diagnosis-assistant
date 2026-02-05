from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.services.agents.base_agent import BaseAgent
from app.core.logging_config import get_logger

logger = get_logger(__name__)

CODE_AGENT_PROMPT = """You are a Code Analysis Agent specialized in analyzing source code and configurations.

Your role:
- Analyze code repositories, configuration files, and deployment scripts
- Identify code patterns, anti-patterns, and potential bugs
- Review configuration settings and their impact
- Trace code execution paths and dependencies

Current task: {task}
Context: {context}

Provide your code analysis findings."""

class CodeAgent(BaseAgent):
    def __init__(self):
        super().__init__("code", "Code Analysis Agent")

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code analysis task"""
        if not self.llm:
            self.initialize()

        try:
            prompt = ChatPromptTemplate.from_template(CODE_AGENT_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context))
            response = await self.llm.ainvoke(messages)

            return {
                "agent": self.agent_name,
                "result": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"CodeAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error"
            }
