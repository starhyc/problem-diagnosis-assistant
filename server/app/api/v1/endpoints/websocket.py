from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import asyncio
from datetime import datetime
import uuid
from app.services.diagnosis_agent import MockDiagnosisAgent
from app.services.qa_agent import QAAgent
from app.services.demo_trace import DemoTraceGenerator
from app.core.logging_config import get_logger

logger = get_logger(__name__)
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
        logger.info(f"WebSocket客户端已连接: {client_id}, 当前连接数: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket客户端已断开: {client_id}, 当前连接数: {len(self.active_connections)}")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
                logger.debug(f"发送消息到 {client_id}: {message.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"发送消息失败 {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        logger.debug(f"广播消息到 {len(self.active_connections)} 个客户端")
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

            logger.info(f"收到WebSocket消息 [{client_id}]: type={message.get('type', 'unknown')}")
            logger.debug(f"消息详情 [{client_id}]: {message}")

            await handle_message(client_id, message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket正常断开: {client_id}")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket错误 [{client_id}]: {e}", exc_info=True)
        manager.disconnect(client_id)


async def handle_message(client_id: str, message: dict):
    message_type = message.get("type")
    data = message.get("data", {})

    logger.info(f"处理消息类型: {message_type} [{client_id}]")

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
        logger.warning(f"未知消息类型: {message_type} [{client_id}]")
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

    logger.info(f"开始诊断 [{client_id}]: agent={agent_type}, symptom={symptom}")

    # Use demo trace generator for trace visualization
    async def ws_send(message: dict):
        if client_id in manager.active_connections:
            await manager.send_message(client_id, message)

    demo_generator = DemoTraceGenerator(ws_send)

    try:
        # Run demo trace in background
        await demo_generator.generate_demo_trace()

        # Also run the original agent for backward compatibility
        agent = AGENT_REGISTRY.get(agent_type, diagnosis_agent)
        async def callback(message: dict):
            if client_id in manager.active_connections:
                await manager.send_message(client_id, message)

        async for event in agent.stream_diagnosis(symptom, description, callback, context):
            pass

        logger.info(f"诊断完成 [{client_id}]: agent={agent_type}")
    except Exception as e:
        logger.error(f"诊断失败 [{client_id}]: agent={agent_type}, error={e}", exc_info=True)
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

