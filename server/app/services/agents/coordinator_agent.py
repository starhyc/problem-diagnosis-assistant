from typing import Dict, Any
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

You MUST ground every conclusion in tool evidence.
- If evidence is insufficient, explicitly output "INSUFFICIENT_EVIDENCE" and list missing evidence.
- Do NOT fabricate facts beyond the tool output.

Current task: {task}
Context: {context}
Tool evidence (mandatory settings query): {tool_evidence}

Provide your analysis and next steps."""


class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("coordinator", "Coordinator Agent", supported_modes=["direct", "plan_execute", "react", "hierarchical"], default_mode="plan_execute")

    @property
    def required_tool_name(self) -> str:
        return "db_query"

    def build_required_tool_input(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "query": "SELECT setting_type, setting_id, enabled FROM settings ORDER BY updated_at DESC",
            "limit": 20,
            "session_id": context.get("session_id", "unknown"),
            "action_id": "coordinator_context",
            "step_id": "mandatory_tool_call",
        }

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.llm:
            self.initialize()

        try:
            tool_record = await self.run_required_tool(task, context)
            prompt = ChatPromptTemplate.from_template(COORDINATOR_PROMPT)
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
            logger.error(f"CoordinatorAgent execution failed: {e}")
            return {
                "agent": self.agent_name,
                "result": str(e),
                "status": "error",
                "model": self._extract_model_name(),
                "inputTokens": 0,
                "outputTokens": 0,
                "costEstimate": 0,
            }
