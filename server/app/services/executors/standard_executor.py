from app.services.executors.base_executor import BaseWorkflowExecutor, DiagnosisState


class StandardExecutor(BaseWorkflowExecutor):
    mode = "prd_standard"

    async def run(self, engine, state: DiagnosisState) -> DiagnosisState:
        return await engine._run_standard(state)
