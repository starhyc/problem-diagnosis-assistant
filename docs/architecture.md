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
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator Agent (主协调者)                      │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │ 状态机   │  │ 决策引擎 │  │ 记忆管理 │  │ 工具调度 │             │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │  │
│  │                                    │                                 │  │
│  │                    ┌───────────────┴───────────────┐                 │  │
│  │                    ▼                             ▼                  │  │
│  │           ┌─────────────┐              ┌─────────────────┐          │  │
│  │           │ Plan Agent  │              │ 任务复杂度评估  │          │  │
│  │           │  (规划者)   │              │                 │          │  │
│  │           └─────────────┘              └─────────────────┘          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                       │
│                    │        Sub-Agents 调度        │                       │
│                    ▼                ▼              ▼                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Log Analyst │  │Code Reviewer│  │ Knowledge   │  │ Metrics     │       │
│  │ 日志分析专家│  │ 代码审查专家│  │ Retriever   │  │ Monitor     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Skill Agents (动态加载)                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │  │
│  │  │ Database    │  │ Network     │  │ Container   │  ... (可扩展)     │  │
│  │  │ Skill Agent │  │ Skill Agent │  │ Skill Agent │                   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
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
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Orchestrator Agent                               │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Phase 1: 问题识别                                              │  │   │
│  │  │ • 解析用户意图                                                 │  │   │
│  │  │ • 识别问题类型                                                 │  │   │
│  │  │ • 构建上下文                                                   │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                      │   │
│  │                              ▼                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Phase 2: 调用 Plan Agent 生成执行计划                          │  │   │
│  │  │                                                               │  │   │
│  │  │  ┌─────────────┐                                              │  │   │
│  │  │  │ Plan Agent  │ ──── 分析任务 ────► 生成计划(DAG/步骤序列)   │  │   │
│  │  │  └─────────────┘                                              │  │   │
│  │  │                                                               │  │   │
│  │  │  返回: Plan { steps[], dependencies[], complexity }           │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                      │   │
│  │                              ▼                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Phase 3: 加载 Skills (根据问题类型动态加载)                     │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         │  根据计划执行步骤                                                  │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Sub-Agents 并行/串行执行                         │   │
│  │                                                                      │   │
│  │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │   │
│  │   │ Log Analyst │   │Code Reviewer│   │ Skill Agent │              │   │
│  │   │   (专家)    │   │   (专家)    │   │  (动态加载) │              │   │
│  │   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘              │   │
│  │          │                 │                 │                      │   │
│  │          ▼                 ▼                 ▼                      │   │
│  │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │   │
│  │   │ Tool        │   │ Tool        │   │ Skill Tools │              │   │
│  │   │ Executor    │   │ Executor    │   │             │              │   │
│  │   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘              │   │
│  │          │                 │                 │                      │   │
│  └──────────┴─────────────────┴─────────────────┴──────────────────────┘   │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Orchestrator Agent                               │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Phase 4: 汇总分析 ────► 生成假设 ────► 验证假设                 │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                      │   │
│  │                              ▼                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Phase 5: 生成报告 ────► WebSocket 推送 ────► 前端展示          │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                      │   │
│  │                              ▼                                      │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ Phase 6: 知识提取 ────► 存储到 Milvus ────► 更新知识库         │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Agent 协作流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Agent 协作流程图                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  用户输入                                                                    │
│     │                                                                       │
│     ▼                                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator Agent (主协调者)                      │  │
│  │                                                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Step 1: 问题识别与意图理解                                     │  │  │
│  │  │         • 解析用户输入                                         │  │  │
│  │  │         • 识别问题领域和类型                                   │  │  │
│  │  │         • 构建初始上下文                                       │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                       │  │
│  │                              ▼                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Step 2: 调用 Plan Agent 生成执行计划                           │  │  │
│  │  │                                                                │  │  │
│  │  │         ┌─────────────────────────────────┐                    │  │  │
│  │  │         │       Plan Agent                │                    │  │  │
│  │  │         │  • 分析任务需求                  │                    │  │  │
│  │  │         │  • 评估任务复杂度                │                    │  │  │
│  │  │         │  • 生成执行计划 (DAG/步骤序列)   │                    │  │  │
│  │  │         │  • 返回计划给 Orchestrator      │                    │  │  │
│  │  │         └─────────────────────────────────┘                    │  │  │
│  │  │                          │                                     │  │  │
│  │  │                          ▼                                     │  │  │
│  │  │         返回: Plan { steps[], dependencies[], priority[] }     │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                       │  │
│  │                              ▼                                       │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Step 3: 执行计划调度                                           │  │  │
│  │  │                                                                │  │  │
│  │  │   ┌─────────────────────────────────────────────────────────┐  │  │  │
│  │  │   │              任务复杂度评估                              │  │  │  │
│  │  │   │                                                         │  │  │  │
│  │  │   │   复杂度 = LOW  ──►  直接调用 Sub-Agent 执行            │  │  │  │
│  │  │   │   复杂度 = HIGH ──►  委托给 Sub-Orchestrator            │  │  │  │
│  │  │   └─────────────────────────────────────────────────────────┘  │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│          ┌───────────────────┼───────────────────┐                         │
│          ▼                   ▼                   ▼                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                 │
│  │ 内置专家     │    │ 内置专家     │    │ Skill Agent  │                 │
│  │ Sub-Agent    │    │ Sub-Agent    │    │ (动态加载)   │                 │
│  │              │    │              │    │              │                 │
│  │ Log Analyst  │    │Code Reviewer │    │ Database     │                 │
│  │ Knowledge    │    │ Metrics      │    │ Network      │                 │
│  │ Retriever    │    │ Monitor      │    │ Container... │                 │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                 │
│         │                   │                   │                          │
│         │                   ▼                   │                          │
│         │           ┌──────────────┐            │                          │
│         │           │Sub-Orchestr. │            │                          │
│         │           │(复杂子任务)  │            │                          │
│         │           │+ Plan Agent  │            │                          │
│         │           └──────┬───────┘            │                          │
│         │                  │                    │                          │
│         └──────────────────┴────────────────────┘                          │
│                            │                                                │
│                            ▼                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator Agent (结果汇总)                      │  │
│  │                                                                       │  │
│  │  Step 4: 收集各 Sub-Agent 结果                                        │  │
│  │  Step 5: 汇总分析，生成假设                                           │  │
│  │  Step 6: 验证假设，定位根因                                           │  │
│  │  Step 7: 生成最终报告                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                            │                                                │
│                            ▼                                                │
│                     输出结果给用户                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 任务复杂度评估策略

| 复杂度级别 | 判断条件 | 处理策略 |
|-----------|---------|---------|
| **LOW** | 单一Agent可完成、无依赖、无需用户交互 | 直接调用Sub-Agent执行 |
| **MEDIUM** | 需要多个Agent协作、有简单依赖 | Orchestrator协调并行/串行执行 |
| **HIGH** | 多阶段任务、复杂依赖、需要用户交互 | 委托给Sub-Orchestrator处理 |

```python
class ComplexityAssessor:
    def assess(self, step: PlanStep, context: Context) -> Complexity:
        factors = {
            "multi_agent": step.requires_multiple_agents,
            "has_dependencies": len(step.dependencies) > 1,
            "needs_interaction": step.needs_user_input,
            "estimated_steps": step.estimated_substeps > 3,
            "domain_specific": step.requires_skill_agent
        }
        
        score = sum(factors.values())
        
        if score >= 3:
            return Complexity.HIGH
        elif score >= 1:
            return Complexity.MEDIUM
        else:
            return Complexity.LOW
```

## 3. 核心组件设计

### 3.1 Agent 层

#### 3.1.1 Orchestrator Agent（协调者）

**职责**：
- 解析用户问题，识别问题类型和意图
- 调用 Plan Agent 生成执行计划
- 根据计划调度 Sub-Agents 执行任务
- 维护全局状态，决策下一步行动
- 汇总结果，生成最终报告

**关键能力**：
- 意图理解与问题分类
- 任务复杂度评估
- 计划执行与调度
- 状态机管理
- 动态决策

```python
class OrchestratorAgent:
    def __init__(self):
        self.state_machine = StateMachine()
        self.memory = MemoryManager()
        self.decision_engine = DecisionEngine()
        self.plan_agent = PlanAgent()
        self.complexity_assessor = ComplexityAssessor()
        self.skill_registry = SkillRegistry()
    
    async def process(self, user_input: str) -> AsyncGenerator[Message, None]:
        state = self.state_machine.current_state
        
        while state != State.END:
            if state == State.PLANNING:
                plan = await self.plan_agent.generate_plan(
                    task=self.current_task,
                    context=self.memory.context
                )
                self.current_plan = plan
                state = self.state_machine.transition(State.EXECUTING)
                continue
            
            if state == State.EXECUTING:
                for step in self.current_plan.steps:
                    complexity = self.complexity_assessor.assess(step, self.memory.context)
                    
                    if complexity == Complexity.HIGH:
                        result = await self.delegate_to_sub_orchestrator(step)
                    else:
                        result = await self.execute_step(step)
                    
                    self.memory.add(result)
                    yield Message(type="step_result", content=result)
                
                state = self.state_machine.transition(State.SUMMARIZING)
                continue
            
            if state == State.SUMMARIZING:
                report = await self.generate_report()
                yield Message(type="final_answer", content=report)
                state = self.state_machine.transition(State.END)
        
        yield Message(type="final_answer", content=self.generate_report())
```

#### 3.1.2 Plan Agent（规划者）

**职责**：
- 分析任务需求，理解问题上下文
- 评估任务复杂度
- 生成结构化的执行计划（DAG 或步骤序列）
- 为每个步骤分配执行策略

**关键能力**：
- 任务分解
- 依赖分析
- 复杂度评估
- 计划优化

```python
class PlanAgent:
    def __init__(self, llm, skill_registry: SkillRegistry):
        self.llm = llm
        self.skill_registry = skill_registry
    
    async def generate_plan(self, task: Task, context: Context) -> Plan:
        available_skills = self.skill_registry.get_relevant_skills(task.domain)
        
        plan = await self.llm.generate(
            prompt=self._build_planning_prompt(task, context, available_skills),
            response_format=Plan
        )
        
        for step in plan.steps:
            step.complexity = self._assess_complexity(step)
            if step.requires_skill:
                step.skill_name = self._match_skill(step, available_skills)
        
        plan.dag = self._build_dag(plan.steps)
        return plan
    
    def _assess_complexity(self, step: PlanStep) -> Complexity:
        factors = [
            step.requires_multiple_agents,
            len(step.dependencies) > 1,
            step.needs_user_interaction,
            step.estimated_substeps > 3
        ]
        return Complexity.HIGH if sum(factors) >= 2 else Complexity.LOW
    
    def _build_dag(self, steps: List[PlanStep]) -> DAG:
        dag = DAG()
        for step in steps:
            dag.add_node(step.id, step)
            for dep in step.dependencies:
                dag.add_edge(dep, step.id)
        return dag

@dataclass
class Plan:
    steps: List[PlanStep]
    dependencies: Dict[str, List[str]]
    dag: Optional[DAG] = None
    estimated_duration: int = 0

@dataclass
class PlanStep:
    id: str
    description: str
    agent_type: str
    params: dict
    dependencies: List[str] = field(default_factory=list)
    complexity: Complexity = Complexity.LOW
    requires_skill: bool = False
    skill_name: Optional[str] = None
    estimated_substeps: int = 1
    needs_user_interaction: bool = False
```

#### 3.1.3 专家 Agent（Sub-Agents）

专家 Agent 分为两类：**内置专家 Agent** 和 **Skill Agent（动态加载）**。

**内置专家 Agent**：

| Agent | 职责 | 工具依赖 |
|-------|------|----------|
| Log Analyst | 日志分析、异常检测 | regex_matcher, time_series_analyzer, log_aggregator |
| Code Reviewer | 代码审查、依赖分析 | static_analyzer, dependency_graph, git_blame |
| Knowledge Retriever | 知识检索、案例推荐 | vector_search, keyword_search |
| Metrics Monitor | 指标监控、性能分析 | prometheus_query, grafana_api |

**Skill Agent（动态加载）**：

| Skill Agent | 职责 | 工具依赖 |
|-------------|------|----------|
| Database Skill | 数据库问题排查 | db_connection_test, slow_query_analyzer, lock_detector |
| Network Skill | 网络问题排查 | ping_test, dns_lookup, trace_route, port_scanner |
| Container Skill | 容器问题排查 | docker_inspect, k8s_describe, log_collector |
| Custom Skill | 用户自定义领域 | 根据技能包定义 |

### 3.2 状态机设计

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  INIT    │─────►│ PLANNING │─────►│ EXECUTING│─────►│HYPOTHESIZE│
│  初始化  │      │  规划    │      │  执行    │      │ 假设生成  │
└──────────┘      └──────────┘      └──────────┘      └────┬─────┘
                                                            │
                                                            ▼
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│   END    │◄─────│  REPORT  │◄─────│SUMMARIZE │◄─────│  VERIFY  │
│  结束    │      │ 生成报告 │      │ 结果汇总 │      │ 验证假设  │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
```

**状态转换条件**：

| 当前状态 | 触发条件 | 目标状态 |
|----------|----------|----------|
| INIT | 用户提交问题 | PLANNING |
| PLANNING | Plan Agent 生成计划完成 | EXECUTING |
| EXECUTING | 所有步骤执行完成 | SUMMARIZE |
| EXECUTING | 执行中需要更多信息 | PLANNING (重新规划) |
| SUMMARIZE | 汇总分析完成 | HYPOTHESIZE |
| HYPOTHESIZE | 假设生成完成 | VERIFY |
| VERIFY | 验证成功 | SUMMARIZE (继续分析) 或 REPORT |
| VERIFY | 验证失败 | HYPOTHESIZE (生成新假设) |
| REPORT | 报告生成完成 | END |

### 3.3 Skill 架构设计

#### 3.3.1 Skill 概念模型

Skill 是领域特定能力的封装，可以动态加载为 Sub-Agent 参与问题排查。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Skill 架构设计                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Skill = 工具集 + 知识库 + Agent行为模板                                     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Skill 结构                                   │   │
│  │                                                                      │   │
│  │  skill_manifest.yaml:                                                │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │ name: database-troubleshooting                                │  │   │
│  │  │ version: 1.0.0                                                │  │   │
│  │  │ description: 数据库问题排查技能                                │  │   │
│  │  │ domain: database                                              │  │   │
│  │  │ tools:                                                        │  │   │
│  │  │   - db_connection_test                                        │  │   │
│  │  │   - slow_query_analyzer                                       │  │   │
│  │  │   - lock_detector                                             │  │   │
│  │  │   - index_advisor                                             │  │   │
│  │  │ knowledge:                                                    │  │   │
│  │  │   collections: [db_errors, db_tuning, db_best_practices]      │  │   │
│  │  │ agent_template:                                               │  │   │
│  │  │   system_prompt: "你是数据库排查专家..."                       │  │   │
│  │  │   decision_patterns:                                          │  │   │
│  │  │     - pattern: "连接超时"                                     │  │   │
│  │  │       actions: [db_connection_test, check_network]            │  │   │
│  │  │     - pattern: "查询慢"                                       │  │   │
│  │  │       actions: [slow_query_analyzer, index_advisor]           │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Skill 加载流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Skill 加载为 Sub-Agent 流程                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                │
│  │ Skill       │      │ Skill       │      │ Skill Agent │                │
│  │ Registry    │─────►│ Loader      │─────►│ Factory     │                │
│  │ (注册中心)  │      │ (加载器)    │      │             │                │
│  └─────────────┘      └─────────────┘      └──────┬──────┘                │
│                                                    │                       │
│                              ┌─────────────────────┴───────────────────┐   │
│                              │                                         │   │
│                              ▼                                         ▼   │
│                     ┌─────────────────┐                    ┌─────────────┐ │
│                     │  Skill Agent    │                    │  Tool Set   │ │
│                     │  Instance       │                    │  (工具实例) │ │
│                     │                 │                    │             │ │
│                     │  • System Prompt│                    │  • Tool 1   │ │
│                     │  • Knowledge    │                    │  • Tool 2   │ │
│                     │  • Patterns     │                    │  • Tool N   │ │
│                     └─────────────────┘                    └─────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.3.3 Skill Registry 设计

```python
class SkillRegistry:
    def __init__(self, storage: SkillStorage):
        self.storage = storage
        self._cache: Dict[str, Skill] = {}
    
    def register(self, skill: Skill) -> None:
        self.storage.save(skill.manifest)
        self._cache[skill.name] = skill
    
    def get_relevant_skills(self, domain: str) -> List[Skill]:
        skills = self.storage.query_by_domain(domain)
        return [self._load_skill(s) for s in skills]
    
    def _load_skill(self, manifest: SkillManifest) -> Skill:
        if manifest.name in self._cache:
            return self._cache[manifest.name]
        
        skill = Skill(
            name=manifest.name,
            version=manifest.version,
            tools=self._load_tools(manifest.tools),
            knowledge=self._load_knowledge(manifest.knowledge),
            agent_template=manifest.agent_template
        )
        self._cache[manifest.name] = skill
        return skill

class SkillAgentFactory:
    def __init__(self, registry: SkillRegistry, llm):
        self.registry = registry
        self.llm = llm
    
    def create_agent(self, skill_name: str) -> SkillAgent:
        skill = self.registry.get(skill_name)
        
        return SkillAgent(
            name=f"{skill.name}_agent",
            llm=self.llm,
            system_prompt=skill.agent_template.system_prompt,
            tools=skill.tools,
            knowledge=skill.knowledge,
            decision_patterns=skill.agent_template.decision_patterns
        )

@dataclass
class Skill:
    name: str
    version: str
    tools: List[Tool]
    knowledge: List[KnowledgeCollection]
    agent_template: AgentTemplate

@dataclass
class AgentTemplate:
    system_prompt: str
    decision_patterns: List[DecisionPattern]

@dataclass
class DecisionPattern:
    pattern: str
    actions: List[str]
    priority: int = 0
```

#### 3.3.4 Skill Agent 执行流程

```python
class SkillAgent:
    def __init__(
        self,
        name: str,
        llm,
        system_prompt: str,
        tools: List[Tool],
        knowledge: List[KnowledgeCollection],
        decision_patterns: List[DecisionPattern]
    ):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.tools = {t.name: t for t in tools}
        self.knowledge = knowledge
        self.decision_patterns = decision_patterns
    
    async def execute(self, task: str, context: Context) -> AgentResult:
        matched_patterns = self._match_patterns(task)
        
        results = []
        for pattern in matched_patterns:
            for action in pattern.actions:
                if action in self.tools:
                    tool = self.tools[action]
                    result = await tool.execute(context)
                    results.append(result)
        
        analysis = await self._analyze_with_llm(task, context, results)
        
        return AgentResult(
            agent_name=self.name,
            analysis=analysis,
            tool_results=results,
            confidence=self._calculate_confidence(results)
        )
    
    def _match_patterns(self, task: str) -> List[DecisionPattern]:
        matched = []
        for pattern in self.decision_patterns:
            if pattern.pattern.lower() in task.lower():
                matched.append(pattern)
        return sorted(matched, key=lambda p: p.priority, reverse=True)
```

### 3.4 记忆管理

#### 3.4.1 短期记忆（Redis）

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

#### 3.4.2 Context 压缩策略

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

### 3.5 工具执行引擎

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
