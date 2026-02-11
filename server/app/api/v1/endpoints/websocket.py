from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
import asyncio
from datetime import datetime
import uuid
from app.core.logging_config import get_logger
from app.core.event_subscriber import EventSubscriber
from app.contracts.diagnosis_protocol import InvalidDiagnosisEvent, normalize_event
from app.services.diagnosis_control_service import diagnosis_control_service

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscribers: Dict[str, EventSubscriber] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}, total: {len(self.active_connections)}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.subscribers:
            try:
                self.subscribers[session_id].stop()
            except Exception as e:
                logger.warning(f"Failed to stop subscriber [{session_id}]: {e}")
            finally:
                del self.subscribers[session_id]
        logger.info(f"WebSocket disconnected: {session_id}, total: {len(self.active_connections)}")

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(normalize_event(message))
            except InvalidDiagnosisEvent as e:
                logger.warning(f"Refused outbound websocket event [{session_id}]: {e}")
            except Exception as e:
                logger.error(f"Send failed {session_id}: {e}")
                self.disconnect(session_id)

    async def subscribe_to_events(self, session_id: str):
        """Subscribe to Redis Pub/Sub events for this session"""
        if session_id in self.subscribers:
            return

        async def event_handler(event: Dict):
            await self.send_message(session_id, event)

        subscriber = EventSubscriber()
        self.subscribers[session_id] = subscriber

        try:
            await subscriber.subscribe_to_diagnosis(session_id, event_handler)
        except Exception as e:
            logger.error(f"Subscribe failed [{session_id}]: {e}", exc_info=True)
            self.subscribers.pop(session_id, None)
            await self.send_message(session_id, {
                "type": "error",
                "data": {"message": f"Failed to subscribe to events: {str(e)}"},
                "timestamp": datetime.now().isoformat()
            })
            raise


manager = ConnectionManager()


@router.websocket("/agent/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = str(uuid.uuid4())
    await manager.connect(websocket, session_id)

    # Send session_id to client
    await manager.send_message(session_id, {
        "type": "connection_established",
        "data": {"session_id": session_id},
        "timestamp": datetime.now().isoformat()
    })

    # Start heartbeat
    heartbeat_task = asyncio.create_task(heartbeat(session_id))

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.info(f"Received [{session_id}]: {message.get('type')}")
            await handle_message(session_id, message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error [{session_id}]: {e}", exc_info=True)
    finally:
        heartbeat_task.cancel()
        manager.disconnect(session_id)


async def heartbeat(session_id: str):
    """Send periodic heartbeat to keep connection alive"""
    while True:
        try:
            await asyncio.sleep(30)
            await manager.send_message(session_id, {
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Heartbeat error [{session_id}]: {e}")
            break


async def handle_message(session_id: str, message: dict):
    message_type = message.get("type")
    data = message.get("data", {})

    if message_type == "start_diagnosis":
        await start_diagnosis(session_id, data)
    elif message_type == "stop_diagnosis":
        await stop_diagnosis(session_id, data)
    elif message_type == "approve_action":
        await approve_action(session_id, data)
    elif message_type == "reject_action":
        await reject_action(session_id, data)
    elif message_type == "pause_diagnosis":
        await pause_diagnosis(session_id, data)
    elif message_type == "resume_diagnosis":
        await resume_diagnosis(session_id, data)
    elif message_type == "confirmation_response":
        await confirmation_response(session_id, data)
    else:
        logger.warning(f"Unknown message type: {message_type}")
        await send_error(session_id, f"Unknown message type: {message_type}")


async def send_message(session_id: str, message_type: str, data: dict):
    message = normalize_event({"type": message_type, "data": data, "timestamp": datetime.now().isoformat()})
    await manager.send_message(session_id, message)


async def send_error(session_id: str, error_message: str):
    await send_message(session_id, "error", {"message": error_message})


async def start_diagnosis(session_id: str, data: dict):
    symptom = data.get("symptom", "")
    mode = data.get("mode", "auto")
    user_id = data.get("user_id", "anonymous")

    logger.info(f"Starting diagnosis [{session_id}]: symptom={symptom}, mode={mode}")

    try:
        await manager.subscribe_to_events(session_id)
        result = diagnosis_control_service.start_diagnosis(
            symptom,
            mode,
            data.get("context"),
            session_id=session_id,
            user_id=user_id,
        )
        await send_message(session_id, "diagnosis_started", {
            "session_id": session_id,
            "task_id": result["task_id"],
            "status": result["status"],
            "command_code": result["command_code"],
        })

    except Exception as e:
        logger.error(f"Failed to start diagnosis [{session_id}]: {e}", exc_info=True)
        await send_error(session_id, f"Failed to start diagnosis: {str(e)}")


async def stop_diagnosis(session_id: str, data: dict):
    result = diagnosis_control_service.stop_diagnosis(session_id)
    await send_message(session_id, "diagnosis_status", {
        "status": "stopped" if result.code == "command_accepted" else "unchanged",
        "session_id": session_id,
        "command_code": result.code,
        "message": result.message,
    })


async def approve_action(session_id: str, data: dict):
    action_id = data.get("actionId", "")
    result = diagnosis_control_service.approve_action(session_id, action_id, source="websocket")
    event_type = "action_approved" if result.code == "command_accepted" else "action_rejected"
    payload = {
        "action_id": action_id,
        "session_id": session_id,
        "command_code": result.code,
        "message": result.message,
    }
    if result.details and result.details.get("risk_level"):
        payload["riskLevel"] = result.details["risk_level"]
    await send_message(session_id, event_type, payload)


async def reject_action(session_id: str, data: dict):
    action_id = data.get("actionId", "")
    reason = data.get("reason", "")
    result = diagnosis_control_service.reject_action(session_id, action_id, reason, source="websocket")
    payload = {
        "action_id": action_id,
        "reason": reason,
        "session_id": session_id,
        "command_code": result.code,
        "message": result.message,
    }
    if result.details and result.details.get("risk_level"):
        payload["riskLevel"] = result.details["risk_level"]
    await send_message(
        session_id,
        "confirmation_rejected" if result.code == "command_accepted" else "action_rejected",
        payload,
    )


async def pause_diagnosis(session_id: str, data: dict):
    result = diagnosis_control_service.pause_diagnosis(session_id)
    await send_message(session_id, "diagnosis_status", {
        "status": "paused" if result.code == "command_accepted" else "unchanged",
        "session_id": session_id,
        "command_code": result.code,
        "message": result.message,
    })


async def resume_diagnosis(session_id: str, data: dict):
    result = diagnosis_control_service.resume_diagnosis(session_id)
    await send_message(session_id, "diagnosis_status", {
        "status": "resumed" if result.code == "command_accepted" else "unchanged",
        "session_id": session_id,
        "command_code": result.code,
        "message": result.message,
    })


async def confirmation_response(session_id: str, data: dict):
    confirmation_id = data.get("confirmationId", "")
    response = data.get("response", {})

    if not confirmation_id:
        await send_error(session_id, "confirmationId is required")
        return

    result = diagnosis_control_service.submit_confirmation_response(
        session_id,
        confirmation_id,
        response,
        source="websocket",
    )

    if result.code == "no_pending_confirmation":
        await send_message(session_id, "confirmation_status", {
            "confirmationId": confirmation_id,
            "status": "pending",
            "action": response.get("action", "approve"),
            "session_id": session_id,
            "command_code": result.code,
            "message": result.message,
            "riskLevel": "R0",
        })
        return

    if result.code == "command_rejected":
        await send_message(session_id, "confirmation_status", {
            "confirmationId": confirmation_id,
            "status": "rejected",
            "action": response.get("action", "approve"),
            "session_id": session_id,
            "command_code": result.code,
            "message": result.message,
            "riskLevel": "R0",
        })
        return

    action = response.get("action", "approve")
    status = "approved" if action == "approve" else "rejected"
    payload = {
        "confirmationId": confirmation_id,
        "status": status,
        "action": action,
        "session_id": session_id,
        "command_code": result.code,
    }
    if result.details and result.details.get("risk_level"):
        payload["riskLevel"] = result.details["risk_level"]
    await send_message(session_id, "confirmation_status", payload)
