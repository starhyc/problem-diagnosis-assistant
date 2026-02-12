# API 设计文档

## 1. API 概述

### 1.1 基础信息

| 项目 | 说明 |
|------|------|
| Base URL | `http://localhost:8000/api/v1` |
| 协议 | HTTP/1.1, WebSocket |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | Bearer Token (JWT) |

### 1.2 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 1.3 错误码定义

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 认证失败 |
| 1003 | 权限不足 |
| 1004 | 资源不存在 |
| 2001 | 会话不存在 |
| 2002 | 会话已结束 |
| 2003 | 会话超时 |
| 3001 | Skill 不存在 |
| 3002 | Skill 执行失败 |
| 4001 | 工具执行超时 |
| 4002 | 工具执行失败 |
| 5001 | LLM 服务错误 |
| 5002 | 向量检索错误 |

## 2. 用户管理 API

### 2.1 用户注册

**POST** `/users/register`

**请求体**：
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2.2 用户登录

**POST** `/users/login`

**请求体**：
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "token": "jwt_token",
    "expires_at": "2024-01-16T10:30:00Z"
  }
}
```

### 2.3 获取用户信息

**GET** `/users/me`

**请求头**：
```
Authorization: Bearer <token>
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z",
    "stats": {
      "total_sessions": 10,
      "successful_analyses": 8
    }
  }
}
```

## 3. 会话管理 API

### 3.1 创建会话

**POST** `/sessions`

**请求头**：
```
Authorization: Bearer <token>
```

**请求体**：
```json
{
  "title": "Pod 重启问题排查",
  "domain": "kubernetes",
  "metadata": {
    "environment": "production",
    "cluster": "prod-cluster-1"
  }
}
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "session_id": "uuid",
    "title": "Pod 重启问题排查",
    "status": "initialized",
    "created_at": "2024-01-15T10:30:00Z",
    "websocket_url": "ws://localhost:8000/ws/sessions/{session_id}"
  }
}
```

### 3.2 获取会话列表

**GET** `/sessions`

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 会话状态: active, completed, failed |
| domain | string | 否 | 问题领域 |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |

**响应**：
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "session_id": "uuid",
        "title": "Pod 重启问题排查",
        "status": "completed",
        "domain": "kubernetes",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:45:00Z",
        "summary": "根因: 内存限制配置过低"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

### 3.3 获取会话详情

**GET** `/sessions/{session_id}`

**响应**：
```json
{
  "code": 0,
  "data": {
    "session_id": "uuid",
    "title": "Pod 重启问题排查",
    "status": "completed",
    "domain": "kubernetes",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:45:00Z",
    "messages": [
      {
        "id": "msg-001",
        "role": "user",
        "content": "我的 Pod 一直重启",
        "timestamp": "2024-01-15T10:30:00Z"
      },
      {
        "id": "msg-002",
        "role": "assistant",
        "content": "正在分析问题...",
        "timestamp": "2024-01-15T10:30:05Z"
      }
    ],
    "result": {
      "root_cause": "内存限制配置过低",
      "confidence": 0.92,
      "evidence": ["日志显示 OOMKilled", "内存限制为 128Mi"],
      "recommendations": ["增加内存限制到 512Mi"]
    }
  }
}
```

### 3.4 删除会话

**DELETE** `/sessions/{session_id}`

**响应**：
```json
{
  "code": 0,
  "message": "Session deleted successfully"
}
```

### 3.5 获取会话历史

**GET** `/sessions/{session_id}/history`

**响应**：
```json
{
  "code": 0,
  "data": {
    "session_id": "uuid",
    "events": [
      {
        "event_id": "evt-001",
        "type": "state_transition",
        "from_state": "init",
        "to_state": "gather",
        "timestamp": "2024-01-15T10:30:00Z"
      },
      {
        "event_id": "evt-002",
        "type": "tool_call",
        "tool_name": "log_analyzer",
        "status": "success",
        "timestamp": "2024-01-15T10:30:10Z"
      }
    ]
  }
}
```

## 4. Skill 管理 API

### 4.1 获取 Skill 列表

**GET** `/skills`

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| domain | string | 否 | 领域过滤 |
| search | string | 否 | 关键词搜索 |

**响应**：
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "skill_id": "k8s-pod-crash-analysis",
        "name": "K8s Pod 崩溃分析",
        "version": "1.2.0",
        "domain": "kubernetes",
        "description": "分析 Kubernetes Pod 崩溃原因",
        "tags": ["k8s", "pod", "crash"],
        "status": "active"
      }
    ],
    "total": 15
  }
}
```

### 4.2 获取 Skill 详情

**GET** `/skills/{skill_id}`

**响应**：
```json
{
  "code": 0,
  "data": {
    "skill_id": "k8s-pod-crash-analysis",
    "name": "K8s Pod 崩溃分析",
    "version": "1.2.0",
    "domain": "kubernetes",
    "description": "分析 Kubernetes Pod 崩溃原因，包括 OOM、镜像拉取失败等",
    "tags": ["k8s", "pod", "crash", "oom", "troubleshooting"],
    "input_schema": {
      "type": "object",
      "required": ["pod_name", "namespace"],
      "properties": {
        "pod_name": {"type": "string", "description": "Pod 名称"},
        "namespace": {"type": "string", "default": "default"},
        "time_range": {"type": "string", "default": "1h"}
      }
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "root_cause": {"type": "string"},
        "evidence": {"type": "array"},
        "recommendations": {"type": "array"},
        "confidence": {"type": "number"}
      }
    },
    "dependencies": {
      "tools": ["kubectl", "log-parser"],
      "knowledge_bases": ["k8s-error-codes"]
    },
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T00:00:00Z"
  }
}
```

### 4.3 注册 Skill

**POST** `/skills`

**请求体**：
```json
{
  "name": "K8s Pod 崩溃分析",
  "domain": "kubernetes",
  "description": "分析 Kubernetes Pod 崩溃原因",
  "tags": ["k8s", "pod", "crash"],
  "input_schema": {},
  "output_schema": {},
  "entrypoint": "skills.k8s.pod_crash:analyze",
  "dependencies": {
    "tools": ["kubectl"],
    "knowledge_bases": ["k8s-error-codes"]
  }
}
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "skill_id": "uuid",
    "name": "K8s Pod 崩溃分析",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 4.4 更新 Skill

**PUT** `/skills/{skill_id}`

**请求体**：
```json
{
  "name": "K8s Pod 崩溃分析 v2",
  "description": "更新后的描述",
  "tags": ["k8s", "pod", "crash", "oom"]
}
```

### 4.5 删除 Skill

**DELETE** `/skills/{skill_id}`

## 5. 工具管理 API

### 5.1 获取工具列表

**GET** `/tools`

**响应**：
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "tool_id": "log-regex-matcher",
        "name": "日志正则匹配",
        "category": "log_analysis",
        "description": "使用正则表达式匹配日志",
        "permission_level": "read-only",
        "status": "active"
      }
    ],
    "total": 20
  }
}
```

### 5.2 执行工具

**POST** `/tools/{tool_id}/execute`

**请求体**：
```json
{
  "session_id": "uuid",
  "params": {
    "pattern": "ERROR.*timeout",
    "log_file": "/var/log/app.log",
    "time_range": "1h"
  },
  "async": true
}
```

**响应（同步）**：
```json
{
  "code": 0,
  "data": {
    "execution_id": "exec-uuid",
    "tool_id": "log-regex-matcher",
    "status": "completed",
    "result": {
      "matches": ["ERROR: connection timeout", "ERROR: request timeout"],
      "count": 2
    },
    "execution_time": 0.5
  }
}
```

**响应（异步）**：
```json
{
  "code": 0,
  "data": {
    "execution_id": "exec-uuid",
    "status": "pending",
    "websocket_channel": "execution:{exec-uuid}"
  }
}
```

### 5.3 获取工具执行状态

**GET** `/tools/executions/{execution_id}`

**响应**：
```json
{
  "code": 0,
  "data": {
    "execution_id": "exec-uuid",
    "tool_id": "log-regex-matcher",
    "status": "running",
    "progress": 45,
    "message": "正在分析第 45/100 条日志...",
    "started_at": "2024-01-15T10:30:00Z",
    "elapsed_time": 12.5
  }
}
```

## 6. 知识库管理 API

### 6.1 获取知识库列表

**GET** `/knowledge/collections`

**响应**：
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "collection_name": "troubleshooting_cases",
        "description": "历史排查案例",
        "document_count": 1000,
        "status": "active"
      }
    ]
  }
}
```

### 6.2 搜索知识

**POST** `/knowledge/search`

**请求体**：
```json
{
  "query": "Pod OOMKilled 解决方案",
  "collections": ["troubleshooting_cases", "technical_docs"],
  "top_k": 5,
  "filters": {
    "domain": "kubernetes"
  }
}
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "results": [
      {
        "id": "doc-001",
        "content": "Pod OOMKilled 通常是因为内存限制设置过低...",
        "score": 0.95,
        "metadata": {
          "source": "k8s-troubleshooting-guide",
          "domain": "kubernetes"
        }
      }
    ],
    "total": 5
  }
}
```

### 6.3 导入知识

**POST** `/knowledge/import`

**请求体**：
```json
{
  "collection": "technical_docs",
  "documents": [
    {
      "content": "文档内容...",
      "metadata": {
        "title": "K8s Pod 故障排查指南",
        "source": "official-docs",
        "domain": "kubernetes"
      }
    }
  ]
}
```

## 7. 健康检查 API

### 7.1 服务健康检查

**GET** `/health`

**响应**：
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "milvus": "healthy",
    "llm": "healthy"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 7.2 就绪检查

**GET** `/ready`

**响应**：
```json
{
  "ready": true,
  "checks": {
    "database": true,
    "redis": true,
    "milvus": true
  }
}
```

## 8. 统计分析 API

### 8.1 获取使用统计

**GET** `/stats/usage`

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 是 | 开始日期 |
| end_date | string | 是 | 结束日期 |
| granularity | string | 否 | 粒度: day, hour |

**响应**：
```json
{
  "code": 0,
  "data": {
    "total_sessions": 100,
    "successful_sessions": 85,
    "avg_resolution_time": 180,
    "token_usage": {
      "input": 50000,
      "output": 20000
    },
    "daily_stats": [
      {
        "date": "2024-01-15",
        "sessions": 10,
        "success_rate": 0.85
      }
    ]
  }
}
```

### 8.2 获取性能指标

**GET** `/stats/performance`

**响应**：
```json
{
  "code": 0,
  "data": {
    "avg_response_time": 2.5,
    "p50_response_time": 1.8,
    "p95_response_time": 5.2,
    "p99_response_time": 10.5,
    "tool_execution_stats": {
      "log_analyzer": {
        "avg_time": 1.2,
        "success_rate": 0.98
      }
    }
  }
}
```

## 9. API 限流

### 9.1 限流规则

| API 类别 | 限流策略 |
|----------|----------|
| 会话创建 | 10 次/分钟 |
| 消息发送 | 60 次/分钟 |
| 工具执行 | 30 次/分钟 |
| 知识检索 | 100 次/分钟 |

### 9.2 限流响应

当触发限流时，返回 HTTP 429：

```json
{
  "code": 429,
  "message": "Rate limit exceeded",
  "data": {
    "retry_after": 60
  }
}
```
