from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional
from datetime import datetime
import asyncio
import uuid


class BaseAgent(ABC):
    def __init__(self):
        self.pending_confirmation: Optional[Dict[str, Any]] = None
        self.confirmation_result: Optional[Dict[str, Any]] = None
        self.paused_for_confirmation = False
        self.is_running = False
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        pass
    
    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass
    
    @abstractmethod
    async def stream_diagnosis(
        self,
        symptom: str,
        description: str,
        callback: callable,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        pass
    
    def handle_confirmation_response(self, confirmation_id: str, response: Dict[str, Any]) -> bool:
        if self.pending_confirmation and self.pending_confirmation.get("id") == confirmation_id:
            self.confirmation_result = response
            self.paused_for_confirmation = False
            self.pending_confirmation = None
            return True
        return False
    
    def get_pending_confirmation(self) -> Optional[Dict[str, Any]]:
        return self.pending_confirmation
    
    def stop(self):
        self.is_running = False
    
    async def send_agent_message(
        self,
        agent_id: str,
        content: str,
        message_type: str,
        callback: callable
    ):
        message = {
            "type": "agent_message",
            "data": {
                "id": str(uuid.uuid4()),
                "agent": agent_id,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "content": content,
                "type": message_type
            },
            "timestamp": datetime.now().isoformat()
        }
        await callback(message)
        return message
    
    async def send_status_update(
        self,
        status: str,
        progress: int,
        current_step: str,
        callback: callable
    ):
        message = {
            "type": "diagnosis_status",
            "data": {
                "status": status,
                "progress": progress,
                "currentStep": current_step
            },
            "timestamp": datetime.now().isoformat()
        }
        await callback(message)
        return message
    
    async def send_confirmation_request(
        self,
        confirmation_data: Dict[str, Any],
        callback: callable
    ):
        message = {
            "type": "confirmation_required",
            "data": confirmation_data,
            "timestamp": datetime.now().isoformat()
        }
        await callback(message)
        return message
    
    async def wait_for_confirmation(self, timeout: int = 300):
        start_time = datetime.now()
        while self.paused_for_confirmation:
            if (datetime.now() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Confirmation timeout after {timeout} seconds")
            await asyncio.sleep(0.5)
