import asyncio
import uuid
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional

from app.core.config import settings


class DemoTraceService:
    """Generate demo agent trace/timeline events for frontend development."""

    def __init__(self, websocket_send: Callable[[dict], Awaitable[None]]):
        self.ws_send = websocket_send

    @property
    def enabled(self) -> bool:
        return settings.enable_demo_trace

    async def generate_demo_trace(self):
        """Generate a complete demo trace flow when feature flag is enabled."""
        if not self.enabled:
            return

        plan_agent_id = f"ag_{uuid.uuid4().hex[:8]}"
        await self._send_trace_start(
            plan_agent_id,
            "plan-agent",
            None,
            "诊断MySQL连接池耗尽问题",
            {"completed": 0, "total": 2},
        )

        await self._send_step(plan_agent_id, "task_received", {"input": "诊断MySQL连接池耗尽问题"})
        await asyncio.sleep(0.5)

        await self._send_step(
            plan_agent_id,
            "llm_thinking",
            {
                "content": "我需要分析这个问题。首先查询数据库连接状态，然后分析日志。",
                "tokens": {"input": 450, "output": 120},
                "cost": 0.0023,
            },
        )
        await asyncio.sleep(1.5)

        sub_agent_1_id = f"ag_{uuid.uuid4().hex[:8]}"
        await self._send_step(
            plan_agent_id,
            "agent_dispatch",
            {
                "targetAgentId": sub_agent_1_id,
                "targetAgentName": "sub-agent-1",
                "taskDescription": "查询数据库连接池状态",
            },
        )
        await asyncio.sleep(0.3)

        await self._send_trace_start(sub_agent_1_id, "sub-agent-1", plan_agent_id, "查询数据库连接池状态")
        await self._send_step(sub_agent_1_id, "task_received", {"input": "查询数据库连接池状态"})
        await asyncio.sleep(0.3)

        await self._send_step(
            sub_agent_1_id,
            "llm_thinking",
            {
                "content": "需要调用query_db工具查询连接池状态",
                "tokens": {"input": 320, "output": 80},
                "cost": 0.0015,
            },
        )
        await asyncio.sleep(1.2)

        await self._send_step(
            sub_agent_1_id,
            "tool_call",
            {
                "toolName": "query_db",
                "toolInput": {"query": "SHOW PROCESSLIST"},
                "toolOutput": {"active_connections": 150, "max_connections": 151},
                "status": "success",
            },
        )
        await asyncio.sleep(0.5)

        await self._send_trace_complete(sub_agent_1_id, "success", 3200, {"input": 320, "output": 80})
        await asyncio.sleep(0.5)

        sub_agent_2_id = f"ag_{uuid.uuid4().hex[:8]}"
        await self._send_step(
            plan_agent_id,
            "agent_dispatch",
            {
                "targetAgentId": sub_agent_2_id,
                "targetAgentName": "sub-agent-2",
                "taskDescription": "分析应用日志",
            },
        )
        await asyncio.sleep(0.3)

        await self._send_trace_start(sub_agent_2_id, "sub-agent-2", plan_agent_id, "分析应用日志")
        await self._send_step(sub_agent_2_id, "task_received", {"input": "分析应用日志"})
        await asyncio.sleep(0.3)

        await self._send_step(
            sub_agent_2_id,
            "tool_call",
            {
                "toolName": "check_metrics",
                "toolInput": {"metric": "connection_errors"},
                "toolOutput": {"error_count": 245, "last_error": "Too many connections"},
                "status": "success",
            },
        )
        await asyncio.sleep(1.8)

        await self._send_step(
            sub_agent_2_id,
            "llm_thinking",
            {
                "content": "发现大量连接错误，建议增加连接池大小",
                "tokens": {"input": 280, "output": 95},
                "cost": 0.0018,
            },
        )
        await asyncio.sleep(0.9)

        await self._send_trace_complete(sub_agent_2_id, "success", 5000, {"input": 280, "output": 95})
        await asyncio.sleep(0.5)

        await self._send_step(
            plan_agent_id,
            "llm_thinking",
            {
                "content": "综合分析：连接池已满(150/151)，建议增加max_connections配置",
                "tokens": {"input": 520, "output": 150},
                "cost": 0.0028,
            },
        )
        await asyncio.sleep(1.0)

        await self._send_trace_complete(plan_agent_id, "success", 15200, {"input": 1570, "output": 445})

    async def _send_trace_start(
        self,
        agent_id: str,
        agent_name: str,
        parent_id: Optional[str] = None,
        task_description: Optional[str] = None,
        subtasks: Optional[Dict[str, int]] = None,
    ):
        data = {
            "agentId": agent_id,
            "agentName": agent_name,
            "parentId": parent_id,
            "startTime": self._get_timestamp(),
        }
        if task_description:
            data["taskDescription"] = task_description
        if subtasks:
            data["subtasks"] = subtasks
        await self.ws_send({"type": "agent_trace_start", "data": data})

    async def _send_step(self, agent_id: str, step_type: str, step_data: Dict[str, Any]):
        step_id = f"step_{uuid.uuid4().hex[:8]}"
        message = {
            "type": "agent_trace_step",
            "data": {
                "agentId": agent_id,
                "id": step_id,
                "type": step_type,
                "timestamp": self._get_timestamp(),
                **step_data,
            },
        }
        if step_type in ["llm_thinking", "tool_call"]:
            message["data"]["duration"] = step_data.get("duration", 1500 if step_type == "llm_thinking" else 500)
        await self.ws_send(message)

    async def _send_trace_complete(self, agent_id: str, status: str, duration: int, total_tokens: Dict[str, int]):
        await self.ws_send(
            {
                "type": "agent_trace_complete",
                "data": {
                    "agentId": agent_id,
                    "status": status,
                    "endTime": self._get_timestamp(),
                    "duration": duration,
                    "totalTokens": total_tokens,
                },
            }
        )

    def _get_timestamp(self) -> str:
        return datetime.utcnow().isoformat() + "Z"
