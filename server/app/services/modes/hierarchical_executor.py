from __future__ import annotations

from typing import Any, Dict, List

from app.services.modes.base_mode_executor import BaseModeExecutor


class HierarchicalExecutor(BaseModeExecutor):
    mode_name = "hierarchical"

    async def execute(self, agent, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        payload = context.copy()
        payload["execution_strategy"] = self.mode_name
        subtasks: List[str] = payload.get("subtasks", [])

        if not subtasks:
            result = await agent.execute(task, payload)
            result.setdefault("mode_trace", []).append(
                {"mode": self.mode_name, "phase": "single_node", "task": task}
            )
            return result

        child_results: List[Dict[str, Any]] = []
        for index, child_task in enumerate(subtasks):
            child_context = {
                **payload,
                "parent_task": task,
                "hierarchy_depth": int(payload.get("hierarchy_depth", 0)) + 1,
                "subtask_index": index,
            }
            child_results.append(await agent.execute(child_task, child_context))

        synthesis_context = {**payload, "child_results": child_results, "hierarchy_phase": "synthesis"}
        synthesis = await agent.execute(f"[SYNTHESIZE] {task}", synthesis_context)
        synthesis.setdefault("meta", {})
        synthesis["meta"]["children"] = child_results
        synthesis["meta"]["mode"] = self.mode_name
        synthesis.setdefault("mode_trace", []).append(
            {
                "mode": self.mode_name,
                "phase": "hierarchical_synthesis",
                "task": task,
                "children": len(child_results),
            }
        )
        return synthesis
