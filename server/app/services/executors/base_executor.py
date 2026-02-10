from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.workflow_engine import DiagnosisWorkflowEngine

DiagnosisState = Dict[str, Any]


class BaseWorkflowExecutor(ABC):
    mode: str

    @abstractmethod
    async def run(self, engine: "DiagnosisWorkflowEngine", state: DiagnosisState) -> DiagnosisState:
        raise NotImplementedError
