from typing import Dict, Any
import json
from langchain_core.prompts import ChatPromptTemplate
from app.services.agents.base_agent import BaseAgent
from app.core.logging_config import get_logger
from app.schemas.events import CoordinationDecision

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

Respond in JSON with keys: summary, coordination_decision.
coordination_decision must include: next_agent, expected_output, stop_condition, rationale."""


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

    def _default_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        available_agents = context.get("available_agents") or ["log", "metric", "code", "knowledge"]
        evidence_count = len(context.get("evidence") or [])
        next_agent = available_agents[0] if available_agents else "coordinator"
        if evidence_count >= 3 and "knowledge" in available_agents:
            next_agent = "knowledge"
        decision = CoordinationDecision(
            next_agent=next_agent,
            expected_output="结构化证据或最终诊断",
            stop_condition=context.get("stop_condition") or "置信度>=85 或关键证据收集完成",
            rationale="基于当前证据密度进行最小增量调度",
        )
        return decision.model_dump()

    def _parse_structured_decision(self, content: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        fallback = self._default_decision(context)
        if not isinstance(content, str):
            return fallback

        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json\n", "", 1)
        try:
            parsed = json.loads(raw)
            decision_payload = parsed.get("coordination_decision") if isinstance(parsed, dict) else None
            if not isinstance(decision_payload, dict):
                return fallback
            decision = CoordinationDecision(**decision_payload)
            return decision.model_dump()
        except Exception:
            return fallback

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.llm:
            self.initialize()

        try:
            tool_record = await self.run_required_tool(task, context)
            prompt = ChatPromptTemplate.from_template(COORDINATOR_PROMPT)
            messages = prompt.format_messages(task=task, context=str(context), tool_evidence=str(tool_record))
            response = await self.llm.ainvoke(messages)
            usage = self._extract_usage(response)
            coordination_decision = self._parse_structured_decision(response.content, context)
            return {
                "agent": self.agent_name,
                "result": response.content,
                "status": "success",
                "coordination_decision": coordination_decision,
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
                "coordination_decision": self._default_decision(context),
                "model": self._extract_model_name(),
                "inputTokens": 0,
                "outputTokens": 0,
                "costEstimate": 0,
            }
