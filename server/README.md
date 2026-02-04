# AIOps 智能诊断平台 - 后端服务

基于 FastAPI 的认证鉴权系统，提供完整的用户管理和权限控制功能。

## 技术栈

- **FastAPI**: 高性能 Web 框架
- **SQLAlchemy**: ORM 数据库操作
- **SQLite**: 轻量级数据库（可替换为 PostgreSQL/MySQL）
- **JWT**: Token 认证
- **Passlib**: 密码加密（Bcrypt）

## 项目结构

```
server/
├── app/
│   ├── api/
│   │   ├── deps.py           # 依赖注入（认证、权限检查）
│   │   └── v1/
│   │       ├── api.py        # API 路由聚合
│   │       └── endpoints/
│   │           └── auth.py   # 认证相关接口
│   ├── core/
│   │   ├── config.py         # 配置管理
│   │   ├── database.py       # 数据库连接
│   │   └── security.py       # 安全相关（JWT、密码加密）
│   ├── models/
│   │   └── user.py           # 用户模型
│   └── schemas/
│       └── user.py           # 数据验证模型
├── main.py                   # 应用入口
├── init_db.py                # 数据库初始化脚本
├── requirements.txt          # Python 依赖
└── .env.example              # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
cd server
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

主要配置项：
- `DATABASE_URL`: 数据库连接字符串
- `SECRET_KEY`: JWT 密钥（生产环境必须修改）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间（分钟）
- `CORS_ORIGINS`: 允许的前端地址

### 3. 初始化数据库

```bash
python init_db.py
```

这将创建数据库表并初始化三个默认用户：
- **admin** / admin123 (管理员)
- **engineer** / engineer123 (工程师)
- **viewer** / viewer123 (观察者)

### 4. 启动服务

开发模式：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

生产模式：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. 访问 API 文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 认证接口

#### 用户注册
```
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "display_name": "测试用户",
  "role": "viewer"
}
```

#### 用户登录
```
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@aiops.com",
    "display_name": "系统管理员",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  }
}
```

#### 获取当前用户信息
```
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

#### 用户登出
```
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
```

## 权限系统

系统支持三种角色，权限从高到低：

1. **admin** (管理员): 所有权限
2. **engineer** (工程师): 可以执行诊断操作
3. **viewer** (观察者): 只读权限

### 权限检查示例

```python
from fastapi import Depends
from app.api.deps import get_current_active_user, require_role

# 需要登录
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

# 需要管理员权限
@router.delete("/users/{user_id}")
async def delete_user(current_user: User = Depends(require_role("admin"))):
    return {"message": "删除成功"}

# 需要工程师或管理员权限
@router.post("/diagnose")
async def diagnose(current_user: User = Depends(require_role("admin", "engineer"))):
    return {"message": "诊断开始"}
```

## 安全特性

1. **密码加密**: 使用 Bcrypt 加密存储密码
2. **JWT Token**: 无状态的 Token 认证机制
3. **CORS 保护**: 配置允许的跨域请求来源
4. **Token 过期**: 可配置的 Token 有效期
5. **用户状态**: 支持禁用用户

## 数据库模型

### User 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String(50) | 用户名（唯一） |
| email | String(100) | 邮箱（唯一） |
| hashed_password | String(255) | 加密后的密码 |
| display_name | String(100) | 显示名称 |
| role | String(20) | 角色 |
| avatar | String(255) | 头像URL |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 常见问题

### 如何修改 JWT 密钥？

编辑 `.env` 文件中的 `SECRET_KEY`，建议使用强随机字符串：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 如何切换到 PostgreSQL？

修改 `.env` 中的数据库连接字符串：
```
DATABASE_URL=postgresql://user:password@localhost:5432/aiops
```

安装 PostgreSQL 驱动：
```bash
pip install psycopg2-binary
```

### 如何添加新的用户角色？

1. 在 `app/models/user.py` 中修改 role 字段的注释
2. 在前端 `src/store/authStore.ts` 中更新 User 类型的 role 字段
3. 在 `src/components/Layout.tsx` 中更新 roleLabels

## 开发建议

1. 使用虚拟环境隔离依赖
2. 定期更新依赖包版本
3. 生产环境使用环境变量管理敏感信息
4. 启用 HTTPS 保护 API 通信
5. 实现请求限流防止暴力破解
6. 添加日志记录和监控

## 许可证

MIT License
