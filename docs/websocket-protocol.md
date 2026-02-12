# WebSocket 协议文档

## 1. 协议概述

### 1.1 连接信息

| 项目 | 说明 |
|------|------|
| WebSocket URL | `ws://localhost:8000/ws/sessions/{session_id}` |
| 协议 | WebSocket over TCP |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | URL 参数传递 token 或首条消息认证 |

### 1.2 连接示例

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/sessions/session-123?token=jwt_token');

ws.onopen = () => {
    console.log('WebSocket connected');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleMessage(message);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
    console.log('WebSocket closed:', event.code, event.reason);
};
```

## 2. 消息类型定义

### 2.1 消息类型枚举

```typescript
enum MessageType {
    THOUGHT = 'thought',                    // Agent 思考过程
    ACTION = 'action',                      // Agent 执行动作
    TOOL_RESULT = 'tool_result',            // 工具执行结果
    STREAM_TOKEN = 'stream_token',          // 流式输出 Token
    FINAL_ANSWER = 'final_answer',          // 最终答案
    USER_INPUT_REQUEST = 'user_input_request', // 请求用户输入
    PROGRESS = 'progress',                  // 进度更新
    ERROR = 'error',                        // 错误消息
    PING = 'ping',                          // 心跳请求
    PONG = 'pong',                          // 心跳响应
    STATE_CHANGE = 'state_change',          // 状态变化
    AGENT_SWITCH = 'agent_switch'           // Agent 切换
}
```

### 2.2 基础消息结构

```typescript
interface BaseMessage {
    type: MessageType;
    session_id: string;
    timestamp: string;
    message_id: string;
}
```

## 3. 详细消息格式

### 3.1 THOUGHT - Agent 思考过程

Agent 在推理过程中的思考内容，用于展示 Agent 的推理链。

```typescript
interface ThoughtMessage extends BaseMessage {
    type: 'thought';
    agent: string;                          // Agent 名称
    content: string;                        // 思考内容
    metadata?: {
        step?: string;                      // 当前步骤
        confidence?: number;                // 置信度
        reasoning_type?: string;            // 推理类型
    };
}
```

**示例**：
```json
{
    "type": "thought",
    "session_id": "sess-123",
    "message_id": "msg-001",
    "timestamp": "2024-01-15T10:30:00Z",
    "agent": "orchestrator",
    "content": "用户报告 Pod 重启问题，需要先确认问题类型。关键词匹配到 'Pod'、'重启'，初步判断为 Kubernetes 领域问题。",
    "metadata": {
        "step": "problem_classification",
        "confidence": 0.85,
        "reasoning_type": "keyword_matching"
    }
}
```

### 3.2 ACTION - Agent 执行动作

Agent 决定执行某个动作（如调用工具、切换 Agent 等）。

```typescript
interface ActionMessage extends BaseMessage {
    type: 'action';
    agent: string;
    action_type: 'tool_call' | 'agent_switch' | 'state_transition';
    action_data: {
        tool_name?: string;
        tool_params?: Record<string, any>;
        target_agent?: string;
        target_state?: string;
    };
    status: 'pending' | 'running' | 'completed' | 'failed';
}
```

**示例**：
```json
{
    "type": "action",
    "session_id": "sess-123",
    "message_id": "msg-002",
    "timestamp": "2024-01-15T10:30:05Z",
    "agent": "orchestrator",
    "action_type": "tool_call",
    "action_data": {
        "tool_name": "kubectl_logs",
        "tool_params": {
            "pod_name": "my-app-xxx",
            "namespace": "default",
            "tail": 500
        }
    },
    "status": "pending"
}
```

### 3.3 TOOL_RESULT - 工具执行结果

工具执行完成后的结果返回。

```typescript
interface ToolResultMessage extends BaseMessage {
    type: 'tool_result';
    tool_name: string;
    execution_id: string;
    status: 'success' | 'failed' | 'timeout';
    result?: Record<string, any>;
    error?: {
        code: string;
        message: string;
        details?: any;
    };
    execution_time_ms: number;
}
```

**示例**：
```json
{
    "type": "tool_result",
    "session_id": "sess-123",
    "message_id": "msg-003",
    "timestamp": "2024-01-15T10:30:08Z",
    "tool_name": "kubectl_logs",
    "execution_id": "exec-001",
    "status": "success",
    "result": {
        "log_count": 500,
        "error_count": 15,
        "error_patterns": ["OOMKilled", "OutOfMemoryError"],
        "last_errors": [
            "java.lang.OutOfMemoryError: Java heap space",
            "Container killed by OOM Killer"
        ]
    },
    "execution_time_ms": 2300
}
```

### 3.4 STREAM_TOKEN - 流式输出 Token

LLM 生成内容的流式输出，实现打字机效果。

```typescript
interface StreamTokenMessage extends BaseMessage {
    type: 'stream_token';
    content_type: 'text' | 'code' | 'markdown';
    token: string;
    sequence: number;
    is_final: boolean;
    delta_text?: string;
}
```

**示例**：
```json
{
    "type": "stream_token",
    "session_id": "sess-123",
    "message_id": "msg-004",
    "timestamp": "2024-01-15T10:30:10Z",
    "content_type": "text",
    "token": "根",
    "sequence": 1,
    "is_final": false,
    "delta_text": "根"
}
```

### 3.5 FINAL_ANSWER - 最终答案

问题排查完成后的最终结果。

```typescript
interface FinalAnswerMessage extends BaseMessage {
    type: 'final_answer';
    root_cause: string;
    evidence: string[];
    recommendations: Array<{
        title: string;
        description: string;
        priority: 'high' | 'medium' | 'low';
        actions?: string[];
    }>;
    confidence: number;
    related_docs?: Array<{
        title: string;
        url?: string;
        snippet: string;
    }>;
    summary: string;
}
```

**示例**：
```json
{
    "type": "final_answer",
    "session_id": "sess-123",
    "message_id": "msg-005",
    "timestamp": "2024-01-15T10:35:00Z",
    "root_cause": "容器内存限制配置过低（128Mi），Java 应用堆内存超出限制，触发 OOM Killer",
    "evidence": [
        "Pod 状态显示 OOMKilled",
        "日志中发现 java.lang.OutOfMemoryError",
        "内存限制配置为 128Mi"
    ],
    "recommendations": [
        {
            "title": "增加内存限制",
            "description": "将容器内存限制增加到至少 512Mi",
            "priority": "high",
            "actions": [
                "修改 Deployment 的 resources.limits.memory",
                "重新部署应用"
            ]
        },
        {
            "title": "优化 JVM 配置",
            "description": "设置合理的 JVM 堆内存参数",
            "priority": "medium",
            "actions": [
                "添加 -Xmx384m -Xms256m 参数",
                "确保堆内存小于容器限制"
            ]
        }
    ],
    "confidence": 0.92,
    "related_docs": [
        {
            "title": "Kubernetes 内存管理最佳实践",
            "url": "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
            "snippet": "容器内存限制应该大于应用实际需要的内存..."
        }
    ],
    "summary": "问题已定位：容器内存限制过低导致 OOM。建议增加内存限制到 512Mi 并优化 JVM 配置。"
}
```

### 3.6 USER_INPUT_REQUEST - 请求用户输入

Agent 需要更多信息时的用户输入请求。

```typescript
interface UserInputRequestMessage extends BaseMessage {
    type: 'user_input_request';
    prompt: string;
    input_type: 'text' | 'select' | 'multiselect' | 'confirm';
    options?: Array<{
        label: string;
        value: string;
        description?: string;
    }>;
    default_value?: string | string[];
    required: boolean;
    timeout_seconds?: number;
}
```

**示例**：
```json
{
    "type": "user_input_request",
    "session_id": "sess-123",
    "message_id": "msg-006",
    "timestamp": "2024-01-15T10:30:15Z",
    "prompt": "请选择问题发生的时间范围：",
    "input_type": "select",
    "options": [
        {"label": "最近 1 小时", "value": "1h"},
        {"label": "最近 6 小时", "value": "6h"},
        {"label": "最近 24 小时", "value": "24h"},
        {"label": "自定义时间", "value": "custom"}
    ],
    "default_value": "1h",
    "required": true,
    "timeout_seconds": 300
}
```

### 3.7 PROGRESS - 进度更新

长时间操作时的进度反馈。

```typescript
interface ProgressMessage extends BaseMessage {
    type: 'progress';
    operation: string;
    progress: number;
    message: string;
    elapsed_seconds: number;
    estimated_remaining_seconds?: number;
}
```

**示例**：
```json
{
    "type": "progress",
    "session_id": "sess-123",
    "message_id": "msg-007",
    "timestamp": "2024-01-15T10:30:20Z",
    "operation": "log_analysis",
    "progress": 45,
    "message": "正在分析第 45/100 条日志...",
    "elapsed_seconds": 12,
    "estimated_remaining_seconds": 15
}
```

### 3.8 ERROR - 错误消息

执行过程中的错误信息。

```typescript
interface ErrorMessage extends BaseMessage {
    type: 'error';
    error_code: string;
    error_message: string;
    error_details?: any;
    recoverable: boolean;
    suggested_action?: string;
}
```

**示例**：
```json
{
    "type": "error",
    "session_id": "sess-123",
    "message_id": "msg-008",
    "timestamp": "2024-01-15T10:30:25Z",
    "error_code": "TOOL_EXECUTION_TIMEOUT",
    "error_message": "工具执行超时",
    "error_details": {
        "tool_name": "kubectl_logs",
        "timeout_seconds": 60
    },
    "recoverable": true,
    "suggested_action": "可以尝试减少日志行数或缩小时间范围"
}
```

### 3.9 STATE_CHANGE - 状态变化

状态机状态转换通知。

```typescript
interface StateChangeMessage extends BaseMessage {
    type: 'state_change';
    from_state: string;
    to_state: string;
    trigger: string;
    metadata?: Record<string, any>;
}
```

**示例**：
```json
{
    "type": "state_change",
    "session_id": "sess-123",
    "message_id": "msg-009",
    "timestamp": "2024-01-15T10:30:30Z",
    "from_state": "gather",
    "to_state": "analyze",
    "trigger": "information_collected",
    "metadata": {
        "tools_executed": 2,
        "data_sources": ["logs", "metrics"]
    }
}
```

### 3.10 AGENT_SWITCH - Agent 切换

当前执行的 Agent 切换通知。

```typescript
interface AgentSwitchMessage extends BaseMessage {
    type: 'agent_switch';
    from_agent: string;
    to_agent: string;
    reason: string;
    task_description?: string;
}
```

**示例**：
```json
{
    "type": "agent_switch",
    "session_id": "sess-123",
    "message_id": "msg-010",
    "timestamp": "2024-01-15T10:30:35Z",
    "from_agent": "orchestrator",
    "to_agent": "log_analyst",
    "reason": "需要专业日志分析",
    "task_description": "分析 Pod 日志中的错误模式"
}
```

## 4. 客户端消息

### 4.1 用户输入响应

```typescript
interface UserInputResponse {
    type: 'user_input_response';
    session_id: string;
    request_id: string;
    value: string | string[];
}
```

**示例**：
```json
{
    "type": "user_input_response",
    "session_id": "sess-123",
    "request_id": "req-001",
    "value": "6h"
}
```

### 4.2 用户消息

```typescript
interface UserMessage {
    type: 'user_message';
    session_id: string;
    content: string;
    metadata?: Record<string, any>;
}
```

**示例**：
```json
{
    "type": "user_message",
    "session_id": "sess-123",
    "content": "我的 Pod 一直重启，日志显示 OOMKilled"
}
```

### 4.3 取消操作

```typescript
interface CancelMessage {
    type: 'cancel';
    session_id: string;
    operation_id?: string;
    reason?: string;
}
```

## 5. 心跳机制

### 5.1 心跳请求

客户端或服务端发送心跳请求：

```json
{
    "type": "ping",
    "session_id": "sess-123",
    "timestamp": "2024-01-15T10:30:40Z"
}
```

### 5.2 心跳响应

```json
{
    "type": "pong",
    "session_id": "sess-123",
    "timestamp": "2024-01-15T10:30:40Z"
}
```

### 5.3 心跳配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 心跳间隔 | 10s | 发送 ping 的间隔 |
| 心跳超时 | 30s | 未收到 pong 的超时时间 |
| 最大重试 | 3 | 超时后重试次数 |

## 6. 断线重连

### 6.1 重连流程

```
┌─────────────────────────────────────────────────────────────────┐
│                       断线重连流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Client                                    Server              │
│    │                                         │                  │
│    │  1. 检测到连接断开                       │                  │
│    │                                         │                  │
│    │  2. 等待重连间隔 (指数退避)              │                  │
│    │                                         │                  │
│    │  3. WebSocket 连接                      │                  │
│    │────────────────────────────────────────►│                  │
│    │  携带 session_id + last_message_id      │                  │
│    │                                         │                  │
│    │  4. 验证会话                            │                  │
│    │◄────────────────────────────────────────│                  │
│    │  返回会话状态                           │                  │
│    │                                         │                  │
│    │  5. 请求丢失消息                        │                  │
│    │────────────────────────────────────────►│                  │
│    │                                         │                  │
│    │  6. 返回丢失的消息                      │                  │
│    │◄────────────────────────────────────────│                  │
│    │                                         │                  │
│    │  7. 继续正常通信                        │                  │
│    │◄───────────────────────────────────────►│                  │
│    │                                         │                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 重连请求

```typescript
interface ReconnectRequest {
    type: 'reconnect';
    session_id: string;
    last_message_id: string;
    auth_token: string;
}
```

**示例**：
```json
{
    "type": "reconnect",
    "session_id": "sess-123",
    "last_message_id": "msg-010",
    "auth_token": "jwt_token"
}
```

### 6.3 重连响应

```typescript
interface ReconnectResponse {
    type: 'reconnect_response';
    session_id: string;
    status: 'success' | 'session_expired' | 'invalid_token';
    current_state: string;
    missed_messages: BaseMessage[];
}
```

## 7. 前端实现示例

### 7.1 WebSocket 客户端类

```typescript
class AgentWebSocketClient {
    private ws: WebSocket | null = null;
    private sessionId: string;
    private token: string;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private messageHandlers: Map<MessageType, (msg: any) => void> = new Map();
    private lastMessageId: string = '';
    
    constructor(sessionId: string, token: string) {
        this.sessionId = sessionId;
        this.token = token;
    }
    
    connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            const url = `ws://localhost:8000/ws/sessions/${this.sessionId}?token=${this.token}`;
            this.ws = new WebSocket(url);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                resolve();
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.stopHeartbeat();
                this.handleDisconnect();
            };
        });
    }
    
    private handleMessage(message: BaseMessage) {
        this.lastMessageId = message.message_id;
        
        const handler = this.messageHandlers.get(message.type);
        if (handler) {
            handler(message);
        }
        
        if (message.type === 'stream_token') {
            this.handleStreamToken(message as StreamTokenMessage);
        }
    }
    
    private handleStreamToken(message: StreamTokenMessage) {
        const textElement = document.getElementById('streaming-text');
        if (textElement && !message.is_final) {
            textElement.textContent += message.token;
        }
    }
    
    on(type: MessageType, handler: (msg: any) => void) {
        this.messageHandlers.set(type, handler);
    }
    
    send(content: string) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'user_message',
                session_id: this.sessionId,
                content
            }));
        }
    }
    
    respondToInput(requestId: string, value: string | string[]) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'user_input_response',
                session_id: this.sessionId,
                request_id: requestId,
                value
            }));
        }
    }
    
    private startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'ping',
                    session_id: this.sessionId,
                    timestamp: new Date().toISOString()
                }));
            }
        }, 10000);
    }
    
    private stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
    }
    
    private handleDisconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
            console.log(`Reconnecting in ${delay}ms...`);
            
            setTimeout(() => {
                this.reconnectAttempts++;
                this.reconnect();
            }, delay);
        }
    }
    
    private async reconnect() {
        try {
            await this.connect();
            
            this.ws?.send(JSON.stringify({
                type: 'reconnect',
                session_id: this.sessionId,
                last_message_id: this.lastMessageId,
                auth_token: this.token
            }));
        } catch (error) {
            console.error('Reconnect failed:', error);
        }
    }
    
    close() {
        this.stopHeartbeat();
        this.ws?.close();
    }
}
```

### 7.2 Vue 3 组合式函数

```typescript
import { ref, onMounted, onUnmounted } from 'vue';

export function useAgentSession(sessionId: string, token: string) {
    const client = ref<AgentWebSocketClient | null>(null);
    const messages = ref<any[]>([]);
    const streamingText = ref('');
    const isConnected = ref(false);
    const currentState = ref('init');
    const currentAgent = ref('');
    
    onMounted(async () => {
        client.value = new AgentWebSocketClient(sessionId, token);
        
        client.value.on('thought', (msg) => {
            messages.value.push(msg);
        });
        
        client.value.on('stream_token', (msg) => {
            streamingText.value += msg.token;
        });
        
        client.value.on('final_answer', (msg) => {
            messages.value.push(msg);
            streamingText.value = '';
        });
        
        client.value.on('state_change', (msg) => {
            currentState.value = msg.to_state;
        });
        
        client.value.on('agent_switch', (msg) => {
            currentAgent.value = msg.to_agent;
        });
        
        await client.value.connect();
        isConnected.value = true;
    });
    
    onUnmounted(() => {
        client.value?.close();
    });
    
    const sendMessage = (content: string) => {
        client.value?.send(content);
    };
    
    const respondToInput = (requestId: string, value: any) => {
        client.value?.respondToInput(requestId, value);
    };
    
    return {
        messages,
        streamingText,
        isConnected,
        currentState,
        currentAgent,
        sendMessage,
        respondToInput
    };
}
```

## 8. 服务端实现示例

### 8.1 FastAPI WebSocket 处理

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/sessions/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str,
    token: str = Query(...)
):
    user = await verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message["type"] == "user_message":
                await handle_user_message(session_id, message, websocket)
            
            elif message["type"] == "user_input_response":
                await handle_user_input_response(session_id, message)
            
            elif message["type"] == "reconnect":
                await handle_reconnect(session_id, message, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

async def handle_user_message(
    session_id: str, 
    message: dict, 
    websocket: WebSocket
):
    await websocket.send_json({
        "type": "state_change",
        "session_id": session_id,
        "message_id": generate_message_id(),
        "timestamp": datetime.utcnow().isoformat(),
        "from_state": "init",
        "to_state": "gather",
        "trigger": "user_message"
    })
    
    async for output in orchestrator.process(message["content"]):
        await websocket.send_json(output)
```
