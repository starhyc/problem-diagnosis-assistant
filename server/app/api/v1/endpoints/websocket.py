from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import asyncio
from datetime import datetime
import uuid
from app.services.diagnosis_agent import MockDiagnosisAgent
from app.services.qa_agent import QAAgent

router = APIRouter()

diagnosis_agent = MockDiagnosisAgent()
qa_agent = QAAgent()

AGENT_REGISTRY = {
    "diagnosis": diagnosis_agent,
    "qa": qa_agent,
}


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"[WebSocket] Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"[WebSocket] Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"[WebSocket] Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/agent/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = f"client-{id(websocket)}"
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            print(f"[WebSocket] Received from {client_id}: {message}")
            
            await handle_message(client_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"[WebSocket] Error for {client_id}: {e}")
        manager.disconnect(client_id)


async def handle_message(client_id: str, message: dict):
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "start_diagnosis":
        await start_diagnosis(client_id, data)
    elif message_type == "stop_diagnosis":
        await stop_diagnosis(client_id, data)
    elif message_type == "approve_action":
        await approve_action(client_id, data)
    elif message_type == "reject_action":
        await reject_action(client_id, data)
    elif message_type == "pause_diagnosis":
        await pause_diagnosis(client_id, data)
    elif message_type == "resume_diagnosis":
        await resume_diagnosis(client_id, data)
    elif message_type == "confirmation_response":
        await handle_confirmation_response(client_id, data)
    else:
        await send_error(client_id, f"Unknown message type: {message_type}")


async def send_message(client_id: str, message_type: str, data: dict):
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    await manager.send_message(client_id, message)


async def send_error(client_id: str, error_message: str):
    await send_message(client_id, "error", {"message": error_message})


async def start_diagnosis(client_id: str, data: dict):
    agent_type = data.get("agent_type", "diagnosis")
    symptom = data.get("symptom", "")
    description = data.get("description", "")
    context = data.get("context", {})
    
    agent = AGENT_REGISTRY.get(agent_type, diagnosis_agent)
    
    async def callback(message: dict):
        if client_id in manager.active_connections:
            await manager.send_message(client_id, message)
    
    try:
        async for event in agent.stream_diagnosis(symptom, description, callback, context):
            pass
    except Exception as e:
        print(f"[WebSocket] Error during {agent_type}: {e}")
        if client_id in manager.active_connections:
            await send_error(client_id, f"{agent_type} failed: {str(e)}")


async def stop_diagnosis(client_id: str, data: dict):
    reason = data.get("reason", "User stopped")
    
    await send_message(client_id, "diagnosis_status", {
        "status": "stopped",
        "progress": 0,
        "currentStep": "Stopped"
    })
    
    await send_message(client_id, "agent_message", {
        "id": str(uuid.uuid4()),
        "agent": "coordinator",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "content": f"诊断已停止: {reason}",
        "type": "info"
    })


async def approve_action(client_id: str, data: dict):
    action_id = data.get("actionId", "")
    
    await send_message(client_id, "agent_message", {
        "id": str(uuid.uuid4()),
        "agent": "coordinator",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "content": f"操作 {action_id} 已批准，正在执行...",
        "type": "action"
    })
    
    await asyncio.sleep(2)
    
    await send_message(client_id, "diagnosis_status", {
        "status": "completed",
        "progress": 100,
        "currentStep": "Completed"
    })


async def reject_action(client_id: str, data: dict):
    action_id = data.get("actionId", "")
    reason = data.get("reason", "")
    
    await send_message(client_id, "agent_message", {
        "id": str(uuid.uuid4()),
        "agent": "coordinator",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "content": f"操作 {action_id} 已拒绝: {reason}",
        "type": "info"
    })


async def pause_diagnosis(client_id: str, data: dict):
    await send_message(client_id, "diagnosis_status", {
        "status": "paused",
        "progress": 0,
        "currentStep": "Paused"
    })


async def resume_diagnosis(client_id: str, data: dict):
    await send_message(client_id, "diagnosis_status", {
        "status": "running",
        "progress": 0,
        "currentStep": "Resumed"
    })


async def handle_confirmation_response(client_id: str, data: dict):
    confirmation_id = data.get("confirmationId", "")
    response_data = data.get("response", {})
    
    success = diagnosis_agent.handle_confirmation_response(confirmation_id, response_data)
    
    if success:
        await send_message(client_id, "agent_message", {
            "id": str(uuid.uuid4()),
            "agent": "coordinator",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "content": f"确认 {confirmation_id} 收到响应，继续诊断...",
            "type": "info"
        })
    else:
        await send_message(client_id, "error", {
            "message": f"无效的确认ID: {confirmation_id}"
        })

