from __future__ import annotations

from typing import Any, Dict

from app.services.modes.base_mode_executor import BaseModeExecutor


class PlanExecuteExecutor(BaseModeExecutor):
    mode_name = "plan_execute"

    async def execute(self, agent, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        payload = context.copy()
        payload["execution_strategy"] = self.mode_name

        plan_context = payload.copy()
        plan_context["plan_phase"] = "plan"
        plan_result = await agent.execute(f"[PLAN] {task}", plan_context)

        execute_context = payload.copy()
        execute_context["plan_phase"] = "execute"
        execute_context["plan_result"] = plan_result.get("result")
        execute_result = await agent.execute(task, execute_context)

        execute_result.setdefault("meta", {})
        execute_result["meta"]["plan"] = plan_result
        execute_result["meta"]["mode"] = self.mode_name
        execute_result.setdefault("mode_trace", []).extend(
            [
                {"mode": self.mode_name, "phase": "plan", "task": task},
                {"mode": self.mode_name, "phase": "execute", "task": task},
            ]
        )
        return execute_result
