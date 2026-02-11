from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.agents.base_agent import BaseAgent


class BaseModeExecutor(ABC):
    """Base strategy for agent mode execution."""

    mode_name: str = "base"

    @abstractmethod
    async def execute(self, agent: "BaseAgent", task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
