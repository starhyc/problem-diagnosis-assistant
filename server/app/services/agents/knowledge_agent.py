from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from app.services.agents.base_agent import BaseAgent
from app.core.logging_config import get_logger

logger = get_logger(__name__)

KNOWLEDGE_AGENT_PROMPT = """You are a Knowledge Agent specialized in querying knowledge graphs and historical cases.

Your role:
- Search knowledge graphs for related patterns and solutions
- Match current symptoms with historical cases
- Retrieve best practices and documented solutions
- Provide confidence scores based on historical success rates

Current task: {task}
Context: {context}

Provide your knowledge-based recommendations."""

class KnowledgeAgent(BaseAgent):
    def __init__(self):
        super().__init__("knowledge", "Knowledge Agent")

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge query task"""
        if not self.llm:
            self.initialize()

        try:
            prompt = ChatPromptTemplate.from_template(KNOWLEDGE_AGENT_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context))
            response = await self.llm.ainvoke(messages)

            return {
                "agent": self.agent_name,
                "result": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"KnowledgeAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error"
            }
