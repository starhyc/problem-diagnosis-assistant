# 项目目录结构

## 整体结构

```
myagent/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py                 # 配置管理
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sessions.py       # 会话管理 API
│   │   │   │   ├── skills.py         # Skill 管理 API
│   │   │   │   ├── users.py          # 用户管理 API
│   │   │   │   └── health.py         # 健康检查 API
│   │   │   └── websocket.py          # WebSocket 处理
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py       # 协调者 Agent
│   │   │   ├── log_analyst.py        # 日志分析专家
│   │   │   ├── code_reviewer.py      # 代码审查专家
│   │   │   ├── knowledge_retriever.py # 知识检索专家
│   │   │   ├── metrics_monitor.py    # 指标监控专家
│   │   │   └── base.py               # Agent 基类
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── state_machine.py      # 状态机
│   │   │   ├── pipeline.py           # Pipeline 编排
│   │   │   ├── memory.py             # 记忆管理
│   │   │   └── context.py            # 上下文管理
│   │   ├── skills/
│   │   │   ├── __init__.py
│   │   │   ├── registry.py           # Skill 注册中心
│   │   │   ├── loader.py             # Skill 加载器
│   │   │   ├── base.py               # Skill 基类
│   │   │   └── domains/              # 领域 Skills
│   │   │       ├── __init__.py
│   │   │       ├── kubernetes/       # K8s 领域
│   │   │       │   ├── __init__.py
│   │   │       │   ├── pod_crash.py
│   │   │       │   └── service_debug.py
│   │   │       ├── database/         # 数据库领域
│   │   │       │   ├── __init__.py
│   │   │       │   ├── slow_query.py
│   │   │       │   └── connection_pool.py
│   │   │       └── frontend/         # 前端领域
│   │   │           ├── __init__.py
│   │   │           └── performance.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── executor.py           # 工具执行引擎
│   │   │   ├── sandbox.py            # 沙箱隔离
│   │   │   ├── registry.py           # 工具注册表
│   │   │   ├── log_tools/            # 日志分析工具
│   │   │   │   ├── __init__.py
│   │   │   │   ├── regex_matcher.py
│   │   │   │   ├── time_series.py
│   │   │   │   └── aggregator.py
│   │   │   ├── code_tools/           # 代码分析工具
│   │   │   │   ├── __init__.py
│   │   │   │   ├── static_analyzer.py
│   │   │   │   └── dependency_graph.py
│   │   │   ├── doc_tools/            # 文档检索工具
│   │   │   │   ├── __init__.py
│   │   │   │   └── vector_search.py
│   │   │   └── monitor_tools/        # 监控查询工具
│   │   │       ├── __init__.py
│   │   │       └── prometheus.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── embeddings.py         # Embedding 生成
│   │   │   ├── retriever.py          # 检索器
│   │   │   ├── indexer.py            # 索引器
│   │   │   └── reranker.py           # 重排序
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── session.py
│   │   │   ├── skill.py
│   │   │   └── trace.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── request.py
│   │   │   ├── response.py
│   │   │   └── websocket.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── session_service.py
│   │   │   ├── llm_service.py
│   │   │   └── knowledge_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       ├── cache.py
│   │       └── security.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_agents/
│   │   ├── test_skills/
│   │   ├── test_tools/
│   │   └── test_api/
│   ├── alembic/                      # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                         # 前端服务
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── ChatInterface.vue     # 聊天界面
│   │   │   ├── MessageList.vue       # 消息列表
│   │   │   ├── StreamingText.vue     # 流式文本
│   │   │   ├── ToolProgress.vue      # 工具进度
│   │   │   └── ReportView.vue        # 报告视图
│   │   ├── composables/
│   │   │   ├── useWebSocket.ts       # WebSocket Hook
│   │   │   └── useSession.ts         # 会话管理 Hook
│   │   ├── stores/
│   │   │   ├── session.ts
│   │   │   └── user.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── styles/
│   │       └── main.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docs/                             # 文档
│   ├── architecture.md               # 技术架构
│   ├── api-design.md                 # API 设计
│   ├── database-design.md            # 数据库设计
│   ├── skill-development-guide.md    # Skill 开发指南
│   ├── websocket-protocol.md         # WebSocket 协议
│   ├── development-setup.md          # 开发环境配置
│   └── project-structure.md          # 项目目录结构
│
├── knowledge/                        # 知识库数据
│   ├── docs/                         # 文档知识
│   │   ├── kubernetes/
│   │   ├── mysql/
│   │   └── redis/
│   ├── errors/                       # 错误码知识
│   │   ├── kubernetes.yaml
│   │   ├── mysql.yaml
│   │   └── http.yaml
│   └── cases/                        # 历史案例
│       └── examples.json
│
├── scripts/                          # 脚本
│   ├── init_db.py                    # 初始化数据库
│   ├── import_knowledge.py           # 导入知识库
│   └── run_dev.sh                    # 开发启动脚本
│
├── docker/                           # Docker 配置
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── nginx.conf
│
├── .env.example
├── .gitignore
├── Makefile
└── README.md
```

## 目录说明

### backend/

后端 Python 服务，基于 FastAPI + AgentScope 构建。

| 子目录 | 说明 |
|--------|------|
| `app/api/` | API 路由和 WebSocket 处理 |
| `app/agents/` | Agent 实现，包括协调者和各领域专家 |
| `app/core/` | 核心组件：状态机、Pipeline、记忆管理 |
| `app/skills/` | Skill 定义和领域 Skills |
| `app/tools/` | 工具实现和执行引擎 |
| `app/rag/` | RAG 相关：Embedding、检索、索引 |
| `app/models/` | 数据库模型 |
| `app/schemas/` | Pydantic Schema 定义 |
| `app/services/` | 业务服务层 |
| `app/utils/` | 工具函数 |

### frontend/

前端 Vue 3 应用，提供类 CLI 的流式交互界面。

| 子目录 | 说明 |
|--------|------|
| `src/components/` | Vue 组件 |
| `src/composables/` | Composition API Hooks |
| `src/stores/` | Pinia 状态管理 |
| `src/types/` | TypeScript 类型定义 |

### docs/

项目文档，包含架构设计、API 规范、开发指南等。

### knowledge/

知识库数据目录，用于 RAG 检索。

### scripts/

开发和运维脚本。

### docker/

Docker 和 Docker Compose 配置文件。
