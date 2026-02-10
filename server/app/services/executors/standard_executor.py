from app.services.executors.base_executor import BaseWorkflowExecutor, DiagnosisState


class StandardExecutor(BaseWorkflowExecutor):
    mode = "plan_execute"

    async def run(self, engine, state: DiagnosisState) -> DiagnosisState:
        return await engine._run_plan_execute(state)
