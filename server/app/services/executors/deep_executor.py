from app.services.executors.base_executor import BaseWorkflowExecutor, DiagnosisState


class DeepExecutor(BaseWorkflowExecutor):
    mode = "react"

    async def run(self, engine, state: DiagnosisState) -> DiagnosisState:
        return await engine._run_react(state)
