from app.services.executors.base_executor import BaseWorkflowExecutor, DiagnosisState


class SwarmExecutor(BaseWorkflowExecutor):
    mode = "hierarchical"

    async def run(self, engine, state: DiagnosisState) -> DiagnosisState:
        return await engine._run_hierarchical(state)
