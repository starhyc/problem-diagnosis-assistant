from app.services.executors.base_executor import BaseWorkflowExecutor, DiagnosisState


class MinimalExecutor(BaseWorkflowExecutor):
    mode = "prd_minimal"

    async def run(self, engine, state: DiagnosisState) -> DiagnosisState:
        return await engine._run_minimal(state)
