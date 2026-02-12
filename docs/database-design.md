# 数据库设计文档

## 1. 数据库概述

### 1.1 存储架构

本系统采用多存储架构：

| 存储类型 | 技术 | 用途 |
|----------|------|------|
| 结构化存储 | PostgreSQL | 用户、会话、Skill 元数据、任务历史 |
| 缓存/队列 | Redis | 会话状态、消息队列、WebSocket 连接管理 |
| 向量存储 | Milvus | RAG 知识库（历史案例、文档、日志等） |

### 1.2 PostgreSQL 版本

- 版本: PostgreSQL 15+
- 扩展: pg_trgm (模糊搜索), uuid-ossp (UUID 生成)

## 2. PostgreSQL 表结构

### 2.1 用户表 (users)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_role CHECK (role IN ('user', 'admin', 'expert')),
    CONSTRAINT chk_status CHECK (status IN ('active', 'inactive', 'suspended'))
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
```

### 2.2 会话表 (sessions)

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    domain VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'initialized',
    current_state VARCHAR(30) NOT NULL DEFAULT 'init',
    metadata JSONB DEFAULT '{}',
    result JSONB,
    confidence_score DECIMAL(3, 2),
    token_usage JSONB DEFAULT '{"input": 0, "output": 0}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_session_status CHECK (
        status IN ('initialized', 'active', 'completed', 'failed', 'timeout')
    ),
    CONSTRAINT chk_session_state CHECK (
        current_state IN ('init', 'gather', 'analyze', 'hypothesize', 'verify', 'root_cause', 'report', 'end')
    )
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_domain ON sessions(domain);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_sessions_user_status ON sessions(user_id, status);
```

### 2.3 消息表 (messages)

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(30) NOT NULL DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_message_role CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    CONSTRAINT chk_message_type CHECK (
        message_type IN ('text', 'thought', 'action', 'tool_result', 'error', 'final_answer')
    )
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_created_at ON messages(session_id, created_at);
```

### 2.4 Skill 表 (skills)

```sql
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    domain VARCHAR(50) NOT NULL,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    dependencies JSONB DEFAULT '{}',
    triggers JSONB DEFAULT '{}',
    execution_config JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_skill_status CHECK (status IN ('active', 'deprecated', 'pending', 'failed')),
    CONSTRAINT uq_skill_version UNIQUE (skill_id, version)
);

CREATE INDEX idx_skills_domain ON skills(domain);
CREATE INDEX idx_skills_status ON skills(status);
CREATE INDEX idx_skills_tags ON skills USING GIN(tags);
```

### 2.5 工具表 (tools)

```sql
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'read-only',
    timeout_seconds INTEGER NOT NULL DEFAULT 60,
    resource_limits JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_tool_permission CHECK (
        permission_level IN ('read-only', 'write', 'admin')
    ),
    CONSTRAINT chk_tool_status CHECK (status IN ('active', 'deprecated', 'disabled'))
);

CREATE INDEX idx_tools_category ON tools(category);
CREATE INDEX idx_tools_status ON tools(status);
```

### 2.6 工具执行记录表 (tool_executions)

```sql
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL UNIQUE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(id),
    skill_id UUID REFERENCES skills(id),
    params JSONB NOT NULL,
    result JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    execution_time_ms INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT chk_execution_status CHECK (
        status IN ('pending', 'running', 'completed', 'failed', 'timeout', 'cancelled')
    )
);

CREATE INDEX idx_tool_executions_session_id ON tool_executions(session_id);
CREATE INDEX idx_tool_executions_tool_id ON tool_executions(tool_id);
CREATE INDEX idx_tool_executions_status ON tool_executions(status);
CREATE INDEX idx_tool_executions_started_at ON tool_executions(started_at DESC);
```

### 2.7 状态转换记录表 (state_transitions)

```sql
CREATE TABLE state_transitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    from_state VARCHAR(30) NOT NULL,
    to_state VARCHAR(30) NOT NULL,
    trigger_type VARCHAR(30) NOT NULL,
    trigger_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_state_transitions_session_id ON state_transitions(session_id);
CREATE INDEX idx_state_transitions_created_at ON state_transitions(session_id, created_at);
```

### 2.8 决策追踪表 (decision_traces)

```sql
CREATE TABLE decision_traces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trace_id UUID NOT NULL UNIQUE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    parent_span_id UUID REFERENCES decision_traces(id),
    span_id UUID NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    decision JSONB,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_trace_status CHECK (status IN ('running', 'completed', 'failed'))
);

CREATE INDEX idx_decision_traces_session_id ON decision_traces(session_id);
CREATE INDEX idx_decision_traces_trace_id ON decision_traces(trace_id);
CREATE INDEX idx_decision_traces_parent_span_id ON decision_traces(parent_span_id);
```

### 2.9 知识库文档表 (knowledge_documents)

```sql
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id VARCHAR(100) NOT NULL UNIQUE,
    collection_name VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    embedding_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    vector_id VARCHAR(100),
    source VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_embedding_status CHECK (
        embedding_status IN ('pending', 'processing', 'completed', 'failed')
    )
);

CREATE INDEX idx_knowledge_documents_collection ON knowledge_documents(collection_name);
CREATE INDEX idx_knowledge_documents_embedding_status ON knowledge_documents(embedding_status);
CREATE INDEX idx_knowledge_documents_source ON knowledge_documents(source);
```

### 2.10 用户反馈表 (user_feedbacks)

```sql
CREATE TABLE user_feedbacks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    feedback_type VARCHAR(30) NOT NULL,
    rating INTEGER,
    comment TEXT,
    is_root_cause_correct BOOLEAN,
    is_solution_helpful BOOLEAN,
    correction_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_feedback_type CHECK (
        feedback_type IN ('rating', 'correction', 'suggestion', 'bug_report')
    ),
    CONSTRAINT chk_rating CHECK (rating >= 1 AND rating <= 5)
);

CREATE INDEX idx_user_feedbacks_session_id ON user_feedbacks(session_id);
CREATE INDEX idx_user_feedbacks_user_id ON user_feedbacks(user_id);
CREATE INDEX idx_user_feedbacks_created_at ON user_feedbacks(created_at DESC);
```

### 2.11 API 密钥表 (api_keys)

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    permissions JSONB DEFAULT '[]',
    rate_limit INTEGER DEFAULT 100,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_api_key_status CHECK (status IN ('active', 'revoked', 'expired'))
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_status ON api_keys(status);
```

### 2.12 审计日志表 (audit_logs)

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_session_id ON audit_logs(session_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

## 3. Redis 数据结构

### 3.1 会话状态

```
Key: session:{session_id}:info
Type: Hash
TTL: 3600s (1 hour)

Fields:
  - user_id: UUID
  - status: string
  - current_state: string
  - created_at: timestamp
  - last_activity: timestamp
```

### 3.2 消息队列

```
Key: session:{session_id}:messages
Type: List
TTL: 3600s

Elements: JSON serialized messages
```

### 3.3 工具执行状态

```
Key: execution:{execution_id}
Type: Hash
TTL: 300s (5 minutes)

Fields:
  - tool_id: UUID
  - session_id: UUID
  - status: string
  - progress: integer
  - message: string
  - started_at: timestamp
```

### 3.4 WebSocket 连接管理

```
Key: ws:connections:{user_id}
Type: Set
TTL: 86400s (24 hours)

Members: session_ids
```

### 3.5 限流计数器

```
Key: ratelimit:{user_id}:{endpoint}
Type: String (Integer)
TTL: 60s

Value: Request count
```

### 3.6 Skill 缓存

```
Key: skill:registry
Type: Hash
TTL: 300s

Fields:
  - {skill_id}: JSON serialized skill metadata
```

## 4. Milvus Collection 设计

### 4.1 troubleshooting_cases

```python
collection_schema = {
    "name": "troubleshooting_cases",
    "description": "历史排查案例",
    "fields": [
        {"name": "id", "type": "VARCHAR", "is_primary": True, "max_length": 36},
        {"name": "case_id", "type": "VARCHAR", "max_length": 100},
        {"name": "problem_vector", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "solution_vector", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "problem_summary", "type": "VARCHAR", "max_length": 2000},
        {"name": "root_cause", "type": "VARCHAR", "max_length": 2000},
        {"name": "solution", "type": "VARCHAR", "max_length": 5000},
        {"name": "domain", "type": "VARCHAR", "max_length": 50},
        {"name": "tags", "type": "ARRAY", "element_type": "VARCHAR", "max_capacity": 20},
        {"name": "success", "type": "BOOL"},
        {"name": "created_at", "type": "INT64"}
    ],
    "indexes": [
        {"field": "problem_vector", "metric": "COSINE"},
        {"field": "solution_vector", "metric": "COSINE"}
    ]
}
```

### 4.2 technical_docs

```python
collection_schema = {
    "name": "technical_docs",
    "description": "技术文档",
    "fields": [
        {"name": "id", "type": "VARCHAR", "is_primary": True, "max_length": 36},
        {"name": "doc_id", "type": "VARCHAR", "max_length": 100},
        {"name": "title_vector", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "content_vector", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "title", "type": "VARCHAR", "max_length": 500},
        {"name": "content", "type": "VARCHAR", "max_length": 10000},
        {"name": "domain", "type": "VARCHAR", "max_length": 50},
        {"name": "source", "type": "VARCHAR", "max_length": 255},
        {"name": "created_at", "type": "INT64"}
    ],
    "indexes": [
        {"field": "title_vector", "metric": "COSINE"},
        {"field": "content_vector", "metric": "COSINE"}
    ]
}
```

### 4.3 error_codes

```python
collection_schema = {
    "name": "error_codes",
    "description": "错误码定义",
    "fields": [
        {"name": "id", "type": "VARCHAR", "is_primary": True, "max_length": 36},
        {"name": "error_code", "type": "VARCHAR", "max_length": 50},
        {"name": "error_vector", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "error_message", "type": "VARCHAR", "max_length": 500},
        {"name": "description", "type": "VARCHAR", "max_length": 2000},
        {"name": "cause", "type": "VARCHAR", "max_length": 2000},
        {"name": "solution", "type": "VARCHAR", "max_length": 2000},
        {"name": "domain", "type": "VARCHAR", "max_length": 50},
        {"name": "severity", "type": "VARCHAR", "max_length": 20}
    ],
    "indexes": [
        {"field": "error_vector", "metric": "COSINE"}
    ]
}
```

### 4.4 log_patterns

```python
collection_schema = {
    "name": "log_patterns",
    "description": "日志模式",
    "fields": [
        {"name": "id", "type": "VARCHAR", "is_primary": True, "max_length": 36},
        {"name": "pattern_id", "type": "VARCHAR", "max_length": 100},
        {"name": "pattern_vector", "type": "FLOAT_VECTOR", "dim": 1536},
        {"name": "pattern", "type": "VARCHAR", "max_length": 500},
        {"name": "description", "type": "VARCHAR", "max_length": 1000},
        {"name": "severity", "type": "VARCHAR", "max_length": 20},
        {"name": "category", "type": "VARCHAR", "max_length": 50},
        {"name": "recommendations", "type": "VARCHAR", "max_length": 2000}
    ],
    "indexes": [
        {"field": "pattern_vector", "metric": "COSINE"}
    ]
}
```

## 5. 数据迁移

### 5.1 Alembic 配置

```ini
# alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://user:pass@localhost/myagent

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

### 5.2 初始迁移脚本

```python
# alembic/versions/001_initial.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('preferences', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
```

## 6. 数据备份策略

### 6.1 PostgreSQL 备份

```bash
#!/bin/bash
# 每日全量备份
pg_dump -h localhost -U postgres myagent | gzip > /backup/myagent_$(date +%Y%m%d).sql.gz

# 保留最近 7 天的备份
find /backup -name "myagent_*.sql.gz" -mtime +7 -delete
```

### 6.2 Redis 备份

```bash
# RDB 快照
redis-cli BGSAVE

# AOF 持久化
# redis.conf
appendonly yes
appendfsync everysec
```

### 6.3 Milvus 备份

```bash
# 使用 Milvus Backup 工具
milvus-backup create -n backup_$(date +%Y%m%d)
```
