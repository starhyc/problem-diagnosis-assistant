# 技术架构文档

## 1. 系统概述

智能问题定位（Root Cause Analysis）Agent 系统是一个通用的故障排查平台，通过多智能体协作、知识检索和工具执行，帮助用户快速定位问题根因。

### 1.1 核心特性

- **领域解耦**：Agent 框架通用，领域知识通过可插拔的 Skills 动态加载
- **智能交互**：流式推理、主动工具调用、持续反馈
- **多源分析**：支持日志分析、代码审查、文档检索、指标监控等多种排查手段

### 1.2 技术栈

| 组件 | 技术选型 | 用途 |
|------|----------|------|
| Agent 框架 | AgentScope | 多智能体协作、Pipeline 编排、记忆管理 |
| 后端 | Python + FastAPI + WebSocket | API 服务、实时通信 |
| 前端 | Vue 3 + WebSocket | 类 CLI 的流式交互界面 |
| 结构化存储 | PostgreSQL | 用户、会话、Skill 元数据、任务历史 |
| 缓存/队列 | Redis | 会话状态、消息队列、WebSocket 连接管理 |
| 向量存储 | Milvus | RAG 知识库（历史案例、文档、日志等） |

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户交互层                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │  Vue 3 CLI  │◄──►│  WebSocket  │◄──►│  FastAPI    │                     │
│  │  流式界面   │    │  实时通信   │    │  API 网关   │                     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘                     │
└───────────────────────────────────────────────┼─────────────────────────────┘
                                                │
┌───────────────────────────────────────────────┼─────────────────────────────┐
│                           AgentScope 编排层                                  │
│  ┌────────────────────────────────────────────▼────────────────────────┐   │
│  │                     Orchestrator Agent (协调者)                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │ 状态机   │  │ 决策引擎 │  │ 记忆管理 │  │ 工具调度 │            │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────┐  ┌─────────────┐  │  ┌─────────────┐  ┌─────────────┐    │
│  │ Log Analyst │  │Code Reviewer│◄─┼─►│ Knowledge   │  │ Metrics     │    │
│  │ 日志分析专家│  │ 代码审查专家│  │  │ Retriever   │  │ Monitor     │    │
│  └─────────────┘  └─────────────┘  │  └─────────────┘  └─────────────┘    │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                           工具执行层                                         │
│  ┌─────────────┐  ┌─────────────┐  │  ┌─────────────┐  ┌─────────────┐     │
│  │ Log Parser  │  │ Static Code │◄─┴─►│ Vector DB   │  │ Prometheus  │     │
│  │ 正则/时序   │  │ Analysis    │     │ (Milvus)    │  │ Grafana API │     │
│  └─────────────┘  └─────────────┘     └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                           存储层                                             │
│  ┌─────────────┐  ┌─────────────┐  │  ┌─────────────┐  ┌─────────────┐     │
│  │ PostgreSQL  │  │   Redis     │◄─┴─►│   Milvus    │  │ 文件系统    │     │
│  │ 结构化存储  │  │ 缓存/队列   │     │ 向量存储    │  │ 日志/配置   │     │
│  └─────────────┘  └─────────────┘     └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据流图                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  用户输入问题                                                                │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────┐                                                           │
│  │ FastAPI     │ ──── 创建会话 ────► Redis (会话状态)                       │
│  │ API Gateway │                                                           │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────┐                                                           │
│  │ Orchestrator│ ──── 问题分类 ────► 加载对应 Skills                        │
│  │ Agent       │                                                           │
│  └──────┬──────┘                                                           │
│         │                                                                   │
│         ├──────────────────┬──────────────────┐                            │
│         ▼                  ▼                  ▼                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │ Log Analyst │    │Code Reviewer│    │ Knowledge   │                     │
│  │             │    │             │    │ Retriever   │                     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│         │                  │                  │                             │
│         ▼                  ▼                  ▼                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │ Tool        │    │ Tool        │    │ Milvus      │                     │
│  │ Executor    │    │ Executor    │    │ Vector DB   │                     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│         │                  │                  │                             │
│         └──────────────────┴──────────────────┘                             │
│                            │                                                │
│                            ▼                                                │
│                     ┌─────────────┐                                        │
│                     │ Orchestrator│ ──── 汇总分析 ────► 生成假设             │
│                     │ Agent       │                                        │
│                     └──────┬──────┘                                        │
│                            │                                                │
│                            ▼                                                │
│                     ┌─────────────┐                                        │
│                     │ 验证假设    │ ──── 调用工具验证 ────► 确认/推翻       │
│                     └──────┬──────┘                                        │
│                            │                                                │
│                            ▼                                                │
│                     ┌─────────────┐                                        │
│                     │ 生成报告    │ ──── WebSocket 推送 ────► 前端展示      │
│                     └──────┬──────┘                                        │
│                            │                                                │
│                            ▼                                                │
│                     ┌─────────────┐                                        │
│                     │ 知识提取    │ ──── 存储到 Milvus ────► 更新知识库     │
│                     └─────────────┘                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. 核心组件设计

### 3.1 Agent 层

#### 3.1.1 Orchestrator Agent（协调者）

**职责**：
- 解析用户问题，识别问题类型
- 规划排查步骤，调度专家 Agent
- 维护全局状态，决策下一步行动
- 汇总结果，生成最终报告

**关键能力**：
- 任务分解
- 状态机管理
- 动态决策

```python
class OrchestratorAgent:
    def __init__(self):
        self.state_machine = StateMachine()
        self.memory = MemoryManager()
        self.decision_engine = DecisionEngine()
    
    async def process(self, user_input: str) -> AsyncGenerator[Message, None]:
        state = self.state_machine.current_state
        
        while state != State.END:
            decision = self.decision_engine.decide(state, self.memory.context)
            
            if decision.action == ActionType.CALL_AGENT:
                result = await self.call_agent(decision.agent, decision.params)
                yield Message(type="agent_result", content=result)
            
            elif decision.action == ActionType.CALL_TOOL:
                result = await self.call_tool(decision.tool, decision.params)
                yield Message(type="tool_result", content=result)
            
            elif decision.action == ActionType.ASK_USER:
                yield Message(type="user_input_request", content=decision.prompt)
                user_response = await self.wait_for_user_input()
                self.memory.add(user_response)
            
            state = self.state_machine.transition(decision.next_state)
        
        yield Message(type="final_answer", content=self.generate_report())
```

#### 3.1.2 专家 Agent

| Agent | 职责 | 工具依赖 |
|-------|------|----------|
| Log Analyst | 日志分析、异常检测 | regex_matcher, time_series_analyzer, log_aggregator |
| Code Reviewer | 代码审查、依赖分析 | static_analyzer, dependency_graph, git_blame |
| Knowledge Retriever | 知识检索、案例推荐 | vector_search, keyword_search |
| Metrics Monitor | 指标监控、性能分析 | prometheus_query, grafana_api |

### 3.2 状态机设计

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  INIT    │─────►│ GATHER   │─────►│ ANALYZE  │─────►│HYPOTHESIZE│
│  初始化  │      │ 信息收集 │      │ 深度分析 │      │ 假设生成  │
└──────────┘      └──────────┘      └──────────┘      └────┬─────┘
                                                            │
                                                            ▼
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│   END    │◄─────│  REPORT  │◄─────│ROOT_CAUSE│◄─────│  VERIFY  │
│  结束    │      │ 生成报告 │      │ 根因定位 │      │ 验证假设  │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
```

**状态转换条件**：

| 当前状态 | 触发条件 | 目标状态 |
|----------|----------|----------|
| INIT | 用户提交问题 | GATHER |
| GATHER | 收集到足够信息 | ANALYZE |
| GATHER | 信息不足 | GATHER (请求用户输入) |
| ANALYZE | 分析完成 | HYPOTHESIZE |
| HYPOTHESIZE | 假设生成完成 | VERIFY |
| VERIFY | 验证成功 | ROOT_CAUSE |
| VERIFY | 验证失败 | HYPOTHESIZE |
| ROOT_CAUSE | 根因确认 | REPORT |
| REPORT | 报告生成完成 | END |

### 3.3 记忆管理

#### 3.3.1 短期记忆（Redis）

```python
class ShortTermMemory:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    def save_session(self, session_id: str, data: dict):
        self.redis.hset(f"session:{session_id}:info", mapping=data)
        self.redis.expire(f"session:{session_id}:info", 3600)
    
    def add_message(self, session_id: str, message: Message):
        self.redis.rpush(
            f"session:{session_id}:messages",
            message.json()
        )
    
    def get_context(self, session_id: str) -> Context:
        messages = self.redis.lrange(f"session:{session_id}:messages", 0, -1)
        return Context(messages=[Message.parse_raw(m) for m in messages])
```

#### 3.3.2 Context 压缩策略

```python
class ContextCompressor:
    def compress(self, context: Context, max_tokens: int) -> Context:
        current_tokens = self.count_tokens(context)
        
        if current_tokens <= max_tokens:
            return context
        
        # Level 1: 工具结果摘要
        context = self.summarize_tool_results(context)
        
        # Level 2: 对话历史滑动窗口
        context = self.apply_sliding_window(context, keep_recent=5)
        
        # Level 3: 语义压缩
        if self.count_tokens(context) > max_tokens:
            context = self.semantic_compress(context)
        
        return context
```

### 3.4 工具执行引擎

```python
class ToolExecutor:
    def __init__(self, sandbox: Sandbox, registry: ToolRegistry):
        self.sandbox = sandbox
        self.registry = registry
    
    async def execute(
        self, 
        tool_name: str, 
        params: dict,
        timeout: int = 60
    ) -> ToolResult:
        tool = self.registry.get(tool_name)
        
        # 权限检查
        if not self.check_permission(tool, params):
            raise PermissionError(f"No permission to execute {tool_name}")
        
        # 输入验证
        validated_params = tool.validate_input(params)
        
        # 沙箱执行
        async with self.sandbox.isolate() as env:
            result = await asyncio.wait_for(
                tool.execute(env, validated_params),
                timeout=timeout
            )
        
        return ToolResult(
            tool_name=tool_name,
            status="success",
            result=result,
            execution_time=result.duration
        )
```

## 4. RAG 架构

### 4.1 知识库组织

```
Milvus Collections:
├── troubleshooting_cases    # 历史排查案例
├── technical_docs           # 技术文档
├── error_codes              # 错误码定义
├── log_patterns             # 日志模式
└── code_snippets            # 代码片段
```

### 4.2 检索流程

```python
class RAGRetriever:
    def __init__(self, milvus: MilvusClient, embedder: Embedder):
        self.milvus = milvus
        self.embedder = embedder
    
    async def retrieve(
        self, 
        query: str, 
        collections: List[str],
        top_k: int = 5
    ) -> List[Document]:
        # 向量化查询
        query_vector = await self.embedder.embed(query)
        
        # 多 Collection 并行检索
        results = await asyncio.gather(*[
            self.milvus.search(
                collection=col,
                vector=query_vector,
                top_k=top_k
            )
            for col in collections
        ])
        
        # 合并和重排序
        merged = self.merge_results(results)
        reranked = await self.rerank(query, merged)
        
        return reranked[:top_k]
```

## 5. 安全架构

### 5.1 多层安全防护

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: 工具白名单                                            │
│  • 只允许预定义的工具执行                                        │
│  • 危险操作需要额外审批                                          │
│  • 工具权限分级: read-only / write / admin                       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: 输入验证                                              │
│  • 参数 Schema 验证                                             │
│  • SQL 注入防护                                                 │
│  • 命令注入防护                                                 │
│  • 路径遍历防护                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: 沙箱隔离                                              │
│  • Docker 容器隔离执行                                          │
│  • 资源限制: CPU/Memory/Network                                 │
│  • 文件系统只读挂载                                             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: 审计日志                                              │
│  • 记录所有工具调用                                             │
│  • 用户身份、时间、参数、结果                                    │
│  • 异常行为告警                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 6. 部署架构

### 6.1 Kubernetes 部署

```yaml
# 部署架构
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                      Ingress Controller                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                           │                               │  │
│  │  ┌─────────────┐    ┌─────┴─────┐    ┌─────────────┐     │  │
│  │  │   Frontend  │    │  Backend  │    │   Agent     │     │  │
│  │  │   (Vue 3)   │    │ (FastAPI) │    │  Workers    │     │  │
│  │  │  3 replicas │    │ 3 replicas│    │ 5 replicas  │     │  │
│  │  └─────────────┘    └───────────┘    └─────────────┘     │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                      Data Layer                           │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐             │  │
│  │  │PostgreSQL │  │   Redis   │  │  Milvus   │             │  │
│  │  │  Primary  │  │  Cluster  │  │  Cluster  │             │  │
│  │  │  + Replica│  │  3 nodes  │  │  3 nodes  │             │  │
│  │  └───────────┘  └───────────┘  └───────────┘             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 资源配置

| 组件 | CPU | Memory | Replicas |
|------|-----|--------|----------|
| Frontend | 0.5 core | 512Mi | 3 |
| Backend API | 1 core | 1Gi | 3 |
| Agent Workers | 2 core | 4Gi | 5 |
| PostgreSQL | 2 core | 4Gi | 1 Primary + 1 Replica |
| Redis | 1 core | 2Gi | 3 |
| Milvus | 4 core | 8Gi | 3 |

## 7. 监控与告警

### 7.1 关键指标

| 指标类别 | 指标名称 | 说明 |
|----------|----------|------|
| 业务指标 | rca_accuracy_rate | 根因定位准确率 |
| 业务指标 | avg_resolution_time | 平均解决时间 |
| 业务指标 | user_satisfaction | 用户满意度 |
| 系统指标 | active_sessions | 活跃会话数 |
| 系统指标 | tool_execution_latency | 工具执行延迟 |
| 系统指标 | llm_token_usage | LLM Token 消耗 |
| 系统指标 | rag_retrieval_latency | RAG 检索延迟 |

### 7.2 告警规则

| 告警名称 | 条件 | 级别 |
|----------|------|------|
| HighErrorRate | 错误率 > 5% | Critical |
| SlowResponse | P99 延迟 > 30s | Warning |
| HighTokenUsage | Token 消耗 > 预算 80% | Warning |
| AgentLoop | 同一会话循环次数 > 10 | Warning |
