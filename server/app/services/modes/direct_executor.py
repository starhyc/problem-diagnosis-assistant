from __future__ import annotations

from typing import Any, Dict

from app.services.modes.base_mode_executor import BaseModeExecutor


class DirectExecutor(BaseModeExecutor):
    mode_name = "direct"

    async def execute(self, agent, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        payload = context.copy()
        payload["execution_strategy"] = self.mode_name
        payload.setdefault("mode_trace", []).append(
            {"mode": self.mode_name, "phase": "single_pass", "task": task}
        )
        return await agent.execute(task, payload)
