from typing import AsyncIterator, Dict, Any, Optional
from datetime import datetime
import asyncio
import uuid
from app.services.agent_base import BaseAgent


class MockDiagnosisAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self._agent_type = "diagnosis"
        self._agent_name = "诊断Agent"
    
    @property
    def agent_type(self) -> str:
        return self._agent_type
    
    @property
    def agent_name(self) -> str:
        return self._agent_name
    
    async def stream_diagnosis(
        self,
        symptom: str,
        description: str,
        callback: callable,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        self.pending_confirmation = None
        self.confirmation_result = None
        self.paused_for_confirmation = False
        
        diagnosis_messages = [
            {
                "delay": 0.5,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "coordinator",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "收到问题报告，开始初始化诊断流程...",
                    "type": "info"
                }
            },
            {
                "delay": 1.5,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "coordinator",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "正在分析问题特征，提取关键症状...",
                    "type": "action"
                }
            },
            {
                "delay": 2.5,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "coordinator",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "基于症状特征，生成以下假设：\n1. 连接池最大连接数配置过小 (概率: 45%)\n2. 存在连接泄漏未正确释放 (概率: 35%)\n3. 数据库查询阻塞导致连接占用 (概率: 20%)",
                    "type": "hypothesis"
                }
            },
            {
                "delay": 3.5,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "log",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "开始扫描ELK日志，时间范围: 最近1小时...",
                    "type": "action"
                }
            },
            {
                "delay": 5.0,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "log",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "发现关键日志:\n```\n[ERROR] HikariPool-1 - Connection is not available, request timed out after 30000ms.\nActive: 100, Idle: 0, Waiting: 47\n```",
                    "type": "evidence"
                }
            },
            {
                "delay": 6.0,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "coordinator",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "证据支持假设1。请求Code Agent分析连接池配置...",
                    "type": "decision"
                }
            },
            {
                "delay": 7.0,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "code",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "正在解析 application.yml 配置文件...",
                    "type": "action"
                }
            },
            {
                "delay": 8.5,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "code",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "配置分析完成:\n```yaml\nspring.datasource.hikari:\n  maximum-pool-size: 100\n  connection-timeout: 30000\n  idle-timeout: 600000\n```\n当前配置在高并发场景下不足",
                    "type": "evidence"
                }
            },
            {
                "delay": 9.5,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "knowledge",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "正在匹配知识库中的相似案例...",
                    "type": "action"
                }
            },
            {
                "delay": 11.0,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "knowledge",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "找到3个相似案例，置信度最高的解决方案：增加连接池大小到300，成功率92%",
                    "type": "evidence"
                }
            },
            {
                "delay": 12.0,
                "message": {
                    "id": str(uuid.uuid4()),
                    "agent": "coordinator",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "content": "诊断完成！\n\n根因：HikariCP连接池配置(100)无法满足当前并发需求\n\n建议解决方案：将maximum-pool-size增加到300\n\n置信度：95%",
                    "type": "decision"
                }
            }
        ]
        
        timeline_steps = [
            {"id": 1, "step": "问题接收", "agent": "coordinator", "status": "pending", "duration": "-", "output": "等待执行"},
            {"id": 2, "step": "假设生成", "agent": "coordinator", "status": "pending", "duration": "-", "output": "等待执行"},
            {"id": 3, "step": "日志分析", "agent": "log", "status": "pending", "duration": "-", "output": "等待执行"},
            {"id": 4, "step": "代码审查", "agent": "code", "status": "pending", "duration": "-", "output": "等待执行"},
            {"id": 5, "step": "知识匹配", "agent": "knowledge", "status": "pending", "duration": "-", "output": "等待执行"},
            {"id": 6, "step": "结论综合", "agent": "coordinator", "status": "pending", "duration": "-", "output": "等待执行"},
        ]
        
        start_time = datetime.now()
        message_index = 0
        timeline_index = 0
        
        await callback({
            "type": "diagnosis_status",
            "data": {
                "status": "running",
                "progress": 0,
                "currentStep": "Initializing"
            },
            "timestamp": datetime.now().isoformat()
        })
        
        yield {
            "type": "diagnosis_status",
            "data": {
                "status": "running",
                "progress": 0,
                "currentStep": "Initializing"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        for item in diagnosis_messages:
            await asyncio.sleep(item["delay"])
            
            message = {
                "type": "agent_message",
                "data": item["message"],
                "timestamp": datetime.now().isoformat()
            }
            
            await callback(message)
            yield message
            
            timeline = timeline_steps.copy()
            if timeline_index < len(timeline):
                if timeline[timeline_index]["status"] == "active":
                    elapsed = (datetime.now() - start_time).total_seconds()
                    timeline[timeline_index] = {
                        **timeline[timeline_index],
                        "status": "completed",
                        "duration": f"{elapsed:.1f}s",
                        "output": item["message"]["content"][:50] + "..."
                    }
                    timeline_index += 1
                
                if timeline_index < len(timeline) and message_index % 2 == 0:
                    timeline[timeline_index] = {
                        **timeline[timeline_index],
                        "status": "active",
                        "duration": "进行中...",
                    }
            
            timeline_update = {
                "type": "timeline_update",
                "data": {"timeline": timeline},
                "timestamp": datetime.now().isoformat()
            }
            
            await callback(timeline_update)
            yield timeline_update
            
            confidence = min(95, int((message_index + 1) / len(diagnosis_messages) * 100))
            confidence_update = {
                "type": "confidence_update",
                "data": {"confidence": confidence},
                "timestamp": datetime.now().isoformat()
            }
            
            await callback(confidence_update)
            yield confidence_update
            
            message_index += 1
            
            if message_index == 4:
                await callback({
                    "type": "diagnosis_status",
                    "data": {
                        "status": "paused",
                        "progress": confidence,
                        "currentStep": "等待用户确认"
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
                yield {
                    "type": "diagnosis_status",
                    "data": {
                        "status": "paused",
                        "progress": confidence,
                        "currentStep": "等待用户确认"
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                confirmation_request = {
                    "type": "confirmation_required",
                    "data": {
                        "id": str(uuid.uuid4()),
                        "actionId": "analyze-logs",
                        "message": "日志分析发现连接池耗尽问题，是否继续进行代码审查？",
                        "description": "基于日志分析，发现 HikariCP 连接池已满（Active: 100, Idle: 0, Waiting: 47）。\n\n建议下一步：\n1. 审查 application.yml 配置文件\n2. 检查是否存在连接泄漏\n3. 分析数据库查询性能",
                        "options": [
                            {"label": "继续代码审查", "value": "continue"},
                            {"label": "跳过代码审查", "value": "skip"},
                            {"label": "修改分析范围", "value": "modify"}
                        ],
                        "defaultOption": "continue",
                        "riskLevel": "low",
                        "timeout": 300
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await callback(confirmation_request)
                yield confirmation_request
                
                self.paused_for_confirmation = True
                self.pending_confirmation = confirmation_request["data"]
                
                while self.paused_for_confirmation:
                    await asyncio.sleep(0.5)
                
                if self.confirmation_result:
                    action = self.confirmation_result.get("action")
                    if action == "continue":
                        await callback({
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "coordinator",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "用户选择继续代码审查，正在分析配置...",
                                "type": "info"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        yield {
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "coordinator",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "用户选择继续代码审查，正在分析配置...",
                                "type": "info"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await asyncio.sleep(1.0)
                        
                        await callback({
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "code",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "正在解析 application.yml 配置文件...",
                                "type": "action"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        yield {
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "code",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "正在解析 application.yml 配置文件...",
                                "type": "action"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await asyncio.sleep(1.5)
                        
                        await callback({
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "code",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "配置分析完成:\n```yaml\nspring.datasource.hikari:\n  maximum-pool-size: 100\n  connection-timeout: 30000\n  idle-timeout: 600000\n```\n当前配置在高并发场景下不足",
                                "type": "evidence"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        yield {
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "code",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "配置分析完成:\n```yaml\nspring.datasource.hikari:\n  maximum-pool-size: 100\n  connection-timeout: 30000\n  idle-timeout: 600000\n```\n当前配置在高并发场景下不足",
                                "type": "evidence"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                    elif action == "skip":
                        await callback({
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "coordinator",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "用户选择跳过代码审查，直接进行知识匹配...",
                                "type": "info"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        yield {
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "coordinator",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "用户选择跳过代码审查，直接进行知识匹配...",
                                "type": "info"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await asyncio.sleep(1.0)
                        
                        await callback({
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "knowledge",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "正在匹配知识库中的相似案例...",
                                "type": "action"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        yield {
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "knowledge",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "正在匹配知识库中的相似案例...",
                                "type": "action"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await asyncio.sleep(1.5)
                        
                        await callback({
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "knowledge",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "找到3个相似案例，置信度最高的解决方案：增加连接池大小到300，成功率92%",
                                "type": "evidence"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        yield {
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "knowledge",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": "找到3个相似案例，置信度最高的解决方案：增加连接池大小到300，成功率92%",
                                "type": "evidence"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        break
                    elif action == "modify":
                        modified_params = self.confirmation_result.get("modifiedParams", {})
                        await callback({
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "coordinator",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": f"用户修改了分析参数: {modified_params}，继续诊断...",
                                "type": "info"
                            },
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        yield {
                            "type": "agent_message",
                            "data": {
                                "id": str(uuid.uuid4()),
                                "agent": "coordinator",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "content": f"用户修改了分析参数: {modified_params}，继续诊断...",
                                "type": "info"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                
                await callback({
                    "type": "diagnosis_status",
                    "data": {
                        "status": "running",
                        "progress": confidence,
                        "currentStep": "继续诊断"
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
                yield {
                    "type": "diagnosis_status",
                    "data": {
                        "status": "running",
                        "progress": confidence,
                        "currentStep": "继续诊断"
                    },
                    "timestamp": datetime.now().isoformat()
                }
        
        action_proposal = {
            "type": "action_proposal",
            "data": {
                "id": "action-1",
                "title": "将连接池大小从100增加到300",
                "description": "基于日志分析和配置审查，建议将maximum-pool-size增加到300",
                "confidence": 95,
                "riskLevel": "low",
                "requiresConfirmation": True,
                "canBeInterrupted": False
            },
            "timestamp": datetime.now().isoformat()
        }
        
        await callback(action_proposal)
        yield action_proposal
        
        completion_status = {
            "type": "diagnosis_status",
            "data": {
                "status": "completed",
                "progress": 100,
                "currentStep": "Completed"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        await callback(completion_status)
        yield completion_status
        
        self.is_running = False
