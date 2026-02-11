from __future__ import annotations

from typing import Any, Dict

from app.services.modes.base_mode_executor import BaseModeExecutor


class ReActExecutor(BaseModeExecutor):
    mode_name = "react"

    async def execute(self, agent, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        payload = context.copy()
        payload["execution_strategy"] = self.mode_name

        max_rounds = int(payload.get("react_max_rounds", 3))
        last_signal = ""
        rounds_without_increment = 0
        traces = []
        final_result: Dict[str, Any] = {}

        for idx in range(max_rounds):
            reason_result = await agent.execute(
                f"[REASON-{idx + 1}] {task}",
                {**payload, "react_phase": "reason", "react_round": idx + 1},
            )
            action_result = await agent.execute(
                f"[ACT-{idx + 1}] {task}",
                {
                    **payload,
                    "react_phase": "act",
                    "react_round": idx + 1,
                    "reasoning": reason_result.get("result"),
                },
            )

            signal = str(action_result.get("result", ""))
            if signal == last_signal:
                rounds_without_increment += 1
            else:
                rounds_without_increment = 0
            last_signal = signal

            traces.append(
                {
                    "mode": self.mode_name,
                    "round": idx + 1,
                    "reason": reason_result.get("result"),
                    "action": action_result.get("result"),
                    "no_increment_rounds": rounds_without_increment,
                }
            )
            final_result = action_result

            if rounds_without_increment >= int(payload.get("react_stagnation_limit", 2)):
                final_result.setdefault("meta", {})
                final_result["meta"]["react_stagnation"] = True
                break

        final_result.setdefault("meta", {})
        final_result["meta"]["mode"] = self.mode_name
        final_result.setdefault("mode_trace", []).extend(traces)
        return final_result
