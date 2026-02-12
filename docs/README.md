# MyAgent - 智能问题定位 Agent 系统

## 项目简介

MyAgent 是一个通用的智能问题定位（Root Cause Analysis）Agent 系统，通过多智能体协作、知识检索和工具执行，帮助用户快速定位问题根因。

### 核心特性

- **领域解耦**：Agent 框架通用，领域知识通过可插拔的 Skills 动态加载
- **智能交互**：流式推理、主动工具调用、持续反馈
- **多源分析**：支持日志分析、代码审查、文档检索、指标监控等多种排查手段

### 技术栈

| 组件 | 技术选型 | 用途 |
|------|----------|------|
| Agent 框架 | AgentScope | 多智能体协作、Pipeline 编排、记忆管理 |
| 后端 | Python + FastAPI + WebSocket | API 服务、实时通信 |
| 前端 | Vue 3 + WebSocket | 类 CLI 的流式交互界面 |
| 结构化存储 | PostgreSQL | 用户、会话、Skill 元数据、任务历史 |
| 缓存/队列 | Redis | 会话状态、消息队列、WebSocket 连接管理 |
| 向量存储 | Milvus | RAG 知识库（历史案例、文档、日志等） |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Poetry (Python 包管理)
- pnpm (前端包管理)

### 安装与启动

```bash
# 克隆项目
git clone https://github.com/your-org/myagent.git
cd myagent

# 使用 Docker Compose 启动所有服务
docker-compose -f docker/docker-compose.dev.yml up -d

# 访问服务
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

详细配置请参考 [开发环境配置文档](docs/development-setup.md)。

## 项目结构

```
myagent/
├── backend/                  # 后端服务 (Python + FastAPI)
│   ├── app/
│   │   ├── agents/          # Agent 实现
│   │   ├── skills/          # Skill 定义
│   │   ├── tools/           # 工具实现
│   │   ├── rag/             # RAG 相关
│   │   └── api/             # API 路由
│   └── tests/               # 测试
├── frontend/                 # 前端服务 (Vue 3)
│   └── src/
│       ├── components/      # Vue 组件
│       ├── composables/     # Composition API
│       └── stores/          # Pinia 状态管理
├── docs/                     # 项目文档
├── knowledge/                # 知识库数据
├── scripts/                  # 脚本
└── docker/                   # Docker 配置
```

详细结构请参考 [项目目录结构文档](docs/project-structure.md)。

## 文档索引

| 文档 | 说明 |
|------|------|
| [技术架构文档](docs/architecture.md) | 系统架构设计、组件交互、数据流 |
| [API 设计文档](docs/api-design.md) | RESTful API 接口规范 |
| [数据库设计文档](docs/database-design.md) | PostgreSQL、Redis、Milvus 数据结构 |
| [Skill 开发指南](docs/skill-development-guide.md) | Skill 定义规范与开发示例 |
| [WebSocket 协议文档](docs/websocket-protocol.md) | WebSocket 消息格式与交互流程 |
| [开发环境配置](docs/development-setup.md) | 本地开发环境搭建指南 |

## 核心架构

### Agent 协作模型

```
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator Agent (协调者)                  │
│  职责: 问题分类、任务调度、结果汇总                               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ Log Analyst   │       │ Code Reviewer │       │ Knowledge     │
│ 日志分析专家   │       │ 代码审查专家   │       │ Retriever     │
└───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
                       ┌───────────────┐
                       │ Metrics       │
                       │ Monitor       │
                       └───────────────┘
```

### 排查流程

```
用户问题 → 问题分类 → 信息收集 → 深度分析 → 假设生成 → 验证假设 → 根因定位 → 生成报告
```

## 开发指南

### 后端开发

```bash
cd backend

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell

# 启动开发服务器
uvicorn app.main:app --reload

# 运行测试
pytest

# 代码检查
ruff check .
```

### 前端开发

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 运行测试
pnpm test

# 代码检查
pnpm lint
```

### Skill 开发

参考 [Skill 开发指南](docs/skill-development-guide.md) 了解如何开发新的领域 Skill。

## 部署

### Docker 部署

```bash
# 构建镜像
docker-compose -f docker/docker-compose.yml build

# 启动服务
docker-compose -f docker/docker-compose.yml up -d
```

### Kubernetes 部署

```bash
# 应用配置
kubectl apply -f k8s/

# 检查状态
kubectl get pods -n myagent
```

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

请确保：
- 代码通过所有测试
- 代码符合项目规范（运行 `ruff check .` 和 `pnpm lint`）
- 更新相关文档

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页: https://github.com/your-org/myagent
- 问题反馈: https://github.com/your-org/myagent/issues
- 邮箱: your-email@example.com
