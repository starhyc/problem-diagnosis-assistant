# 开发环境配置文档

## 1. 环境要求

### 1.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10/11, macOS 12+, Ubuntu 20.04+ | - |
| CPU | 4 核 | 8 核+ |
| 内存 | 8 GB | 16 GB+ |
| 磁盘 | 50 GB | 100 GB+ SSD |

### 1.2 软件依赖

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| Python | 3.10+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| Docker | 24.0+ | 容器化部署 |
| Docker Compose | 2.20+ | 本地开发环境 |
| Git | 2.40+ | 版本控制 |
| Poetry | 1.7+ | Python 依赖管理 |
| pnpm | 8.0+ | 前端包管理 |

## 2. 快速开始

### 2.1 克隆项目

```bash
git clone https://github.com/your-org/myagent.git
cd myagent
```

### 2.2 使用 Docker Compose 启动

```bash
# 启动所有服务
docker-compose -f docker/docker-compose.dev.yml up -d

# 查看服务状态
docker-compose -f docker/docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker/docker-compose.dev.yml logs -f backend
```

### 2.3 访问服务

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| AgentScope Studio | http://localhost:5000 |

## 3. 本地开发配置

### 3.1 后端配置

#### 3.1.1 安装 Python 依赖

```bash
cd backend

# 使用 Poetry 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

#### 3.1.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
vim .env
```

**.env 文件内容**：

```env
# 应用配置
APP_NAME=MyAgent
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/myagent
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis 配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_PREFIX=myagent_

# LLM 配置
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_API_KEY=your-openai-api-key
LLM_API_BASE=https://api.openai.com/v1
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Embedding 配置
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# WebSocket 配置
WS_HEARTBEAT_INTERVAL=10
WS_HEARTBEAT_TIMEOUT=30

# 工具执行配置
TOOL_EXECUTION_TIMEOUT=60
TOOL_SANDBOX_ENABLED=true

# 日志配置
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

#### 3.1.3 初始化数据库

```bash
# 创建数据库
createdb myagent

# 运行迁移
alembic upgrade head

# 初始化种子数据
python scripts/init_db.py
```

#### 3.1.4 启动开发服务器

```bash
# 启动 FastAPI 开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用脚本
python -m app.main
```

### 3.2 前端配置

#### 3.2.1 安装依赖

```bash
cd frontend

# 使用 pnpm 安装依赖
pnpm install
```

#### 3.2.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env.local
```

**.env.local 文件内容**：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_APP_TITLE=MyAgent
```

#### 3.2.3 启动开发服务器

```bash
# 启动 Vite 开发服务器
pnpm dev

# 或指定端口
pnpm dev --port 3000
```

### 3.3 基础设施服务

#### 3.3.1 PostgreSQL

```bash
# 使用 Docker 启动
docker run -d \
  --name myagent-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=myagent \
  -p 5432:5432 \
  postgres:15

# 连接测试
psql -h localhost -U postgres -d myagent
```

#### 3.3.2 Redis

```bash
# 使用 Docker 启动
docker run -d \
  --name myagent-redis \
  -p 6379:6379 \
  redis:7-alpine

# 连接测试
redis-cli ping
```

#### 3.3.3 Milvus

```bash
# 使用 Docker Compose 启动 Milvus
wget https://github.com/milvus-io/milvus/releases/download/v2.3.0/milvus-standalone-docker-compose.yml -O docker-compose.milvus.yml

docker-compose -f docker-compose.milvus.yml up -d

# 安装 Milvus CLI
pip install milvus-cli

# 连接测试
milvus_cli
> connect --host localhost --port 19530
```

## 4. IDE 配置

### 4.1 VS Code 配置

#### 4.1.1 推荐扩展

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "Vue.volar",
    "Vue.vscode-typescript-vue-plugin",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml",
    "tamasfe.even-better-toml"
  ]
}
```

#### 4.1.2 工作区配置

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[vue]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  }
}
```

### 4.2 PyCharm 配置

1. 打开项目根目录
2. 设置 Python 解释器：`backend/.venv/bin/python`
3. 启用 Ruff 插件
4. 配置 Django/Flask 支持（如适用）

## 5. 代码规范

### 5.1 Python 代码规范

#### 5.1.1 使用 Ruff

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]
ignore = [
    "E501",   # line too long
    "B008",   # do not perform function calls in argument defaults
]

[tool.ruff.lint.isort]
known-first-party = ["app"]
```

#### 5.1.2 格式化命令

```bash
# 检查代码
ruff check .

# 自动修复
ruff check . --fix

# 格式化
ruff format .
```

### 5.2 TypeScript/Vue 代码规范

#### 5.2.1 ESLint 配置

```javascript
// .eslintrc.cjs
module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
    es2022: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    '@vue/eslint-config-typescript',
    '@vue/eslint-config-prettier',
  ],
  rules: {
    'vue/multi-word-component-names': 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
};
```

#### 5.2.2 Prettier 配置

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

#### 5.2.3 格式化命令

```bash
# 检查代码
pnpm lint

# 自动修复
pnpm lint:fix

# 格式化
pnpm format
```

## 6. 测试配置

### 6.1 后端测试

#### 6.1.1 pytest 配置

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow running tests",
]
```

#### 6.1.2 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 6.2 前端测试

#### 6.2.1 Vitest 配置

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
```

#### 6.2.2 运行测试

```bash
# 运行所有测试
pnpm test

# 运行测试并监视变化
pnpm test:watch

# 生成覆盖率报告
pnpm test:coverage
```

## 7. Git 配置

### 7.1 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Environment variables
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Node
node_modules/
.pnpm-store/

# Build
dist/
*.local

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/
.nyc_output/

# Milvus
milvus-data/
```

### 7.2 Git Hooks

使用 pre-commit 进行代码检查：

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

安装 hooks：

```bash
pre-commit install
```

## 8. Docker 配置

### 8.1 开发环境 Docker Compose

```yaml
# docker/docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: myagent
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  milvus:
    image: milvusdb/milvus:v2.3.0
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - "19530:19530"
    volumes:
      - milvus_data:/var/lib/milvus
    depends_on:
      - etcd
      - minio

  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      ETCD_AUTO_COMPACTION_MODE: revision
      ETCD_AUTO_COMPACTION_RETENTION: '1000'
      ETCD_QUOTA_BACKEND_BYTES: '4294967296'
    volumes:
      - etcd_data:/etcd

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    command: server /minio_data
    volumes:
      - minio_data:/minio_data

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile.dev
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/myagent
      REDIS_URL: redis://redis:6379/0
      MILVUS_HOST: milvus
      MILVUS_PORT: 19530
    ports:
      - "8000:8000"
    volumes:
      - ../backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      milvus:
        condition: service_started

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ../frontend:/app
      - /app/node_modules
    environment:
      VITE_API_BASE_URL: http://localhost:8000
      VITE_WS_BASE_URL: ws://localhost:8000

volumes:
  postgres_data:
  redis_data:
  milvus_data:
  etcd_data:
  minio_data:
```

### 8.2 后端开发 Dockerfile

```dockerfile
# backend/Dockerfile.dev
FROM python:3.10-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 8.3 前端开发 Dockerfile

```dockerfile
# frontend/Dockerfile.dev
FROM node:18-alpine

WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-lock.yaml ./
RUN pnpm install

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev", "--host", "0.0.0.0"]
```

## 9. 常见问题

### 9.1 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 检查连接
psql -h localhost -U postgres -d myagent

# 重启服务
docker-compose -f docker/docker-compose.dev.yml restart postgres
```

### 9.2 Milvus 连接失败

```bash
# 检查 Milvus 状态
docker logs myagent-milvus-1

# 重启 Milvus
docker-compose -f docker/docker-compose.dev.yml restart milvus
```

### 9.3 前端无法连接后端

1. 检查后端是否运行：`curl http://localhost:8000/health`
2. 检查 CORS 配置
3. 检查前端环境变量配置

### 9.4 LLM API 调用失败

1. 检查 API Key 是否正确
2. 检查网络连接
3. 检查 API 配额是否用尽

## 10. 开发工作流

### 10.1 日常开发流程

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 创建功能分支
git checkout -b feature/new-skill

# 3. 启动开发环境
docker-compose -f docker/docker-compose.dev.yml up -d

# 4. 开发代码
# ...

# 5. 运行测试
pytest
pnpm test

# 6. 代码检查
ruff check .
pnpm lint

# 7. 提交代码
git add .
git commit -m "feat: add new skill for database analysis"

# 8. 推送分支
git push origin feature/new-skill

# 9. 创建 Pull Request
```

### 10.2 Makefile 命令

```makefile
.PHONY: all install dev test lint clean

all: install dev

install:
	cd backend && poetry install
	cd frontend && pnpm install

dev:
	docker-compose -f docker/docker-compose.dev.yml up -d
	cd backend && poetry run uvicorn app.main:app --reload
	cd frontend && pnpm dev

test:
	cd backend && poetry run pytest
	cd frontend && pnpm test

lint:
	cd backend && poetry run ruff check .
	cd frontend && pnpm lint

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```
