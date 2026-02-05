from typing import Dict, Any
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from app.services.agents.base_agent import BaseAgent
from app.core.logging_config import get_logger

logger = get_logger(__name__)

COORDINATOR_PROMPT = """You are a Coordinator Agent responsible for orchestrating the diagnosis process.

Your role:
- Analyze the symptom and determine which specialized agents to invoke
- Synthesize results from multiple agents
- Make final diagnosis decisions
- Generate action recommendations

Current task: {task}
Context: {context}

Provide your analysis and next steps."""

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("coordinator", "Coordinator Agent")

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coordinator task"""
        if not self.llm:
            self.initialize()

        try:
            prompt = ChatPromptTemplate.from_template(COORDINATOR_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context))
            response = await self.llm.ainvoke(messages)

            return {
                "agent": self.agent_name,
                "result": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"CoordinatorAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error"
            }
