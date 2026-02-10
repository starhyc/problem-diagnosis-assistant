from app.services.executors.base_executor import BaseWorkflowExecutor, DiagnosisState


class SwarmExecutor(BaseWorkflowExecutor):
    mode = "prd_swarm"

    async def run(self, engine, state: DiagnosisState) -> DiagnosisState:
        return await engine._run_swarm(state)
