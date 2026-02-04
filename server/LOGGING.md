# 日志系统说明

## 概述

服务器已配置详细的日志系统，使用Python标准logging模块，支持控制台和文件输出。

## 配置

### 环境变量

在 `.env` 文件中配置：

```env
LOG_LEVEL=INFO          # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/aiops.log # 日志文件路径
```

### 日志级别

- **DEBUG**: 详细的调试信息（WebSocket消息详情、Token验证等）
- **INFO**: 一般信息（用户登录、诊断启动、API调用等）
- **WARNING**: 警告信息（登录失败、未找到资源等）
- **ERROR**: 错误信息（异常、失败的操作等）

## 日志内容

### 1. 认证相关 (auth.py)
- 用户注册请求和结果
- 登录成功/失败（含失败原因）
- 用户退出
- Token验证失败详情

### 2. WebSocket通信 (websocket.py)
- 客户端连接/断开（含连接数统计）
- 收到的消息类型
- 消息处理详情
- 发送消息到客户端
- WebSocket错误和异常

### 3. 诊断流程 (diagnosis_agent.py)
- 诊断开始（症状、描述）
- 诊断完成
- 诊断过程中的错误

### 4. API端点
- Dashboard数据查询
- Investigation操作（启动/停止诊断、操作批准/拒绝）
- Knowledge查询（历史案例）
- Settings更新（红线配置）

### 5. 权限控制 (deps.py)
- Token验证成功/失败
- 权限不足警告

## 日志格式

```
2026-02-04 10:30:45 - app.api.v1.endpoints.auth - INFO - 登录成功: username=admin, role=管理员
2026-02-04 10:30:50 - app.api.v1.endpoints.websocket - INFO - WebSocket客户端已连接: client-123, 当前连接数: 1
2026-02-04 10:31:00 - app.services.diagnosis_agent - INFO - 开始诊断流程: symptom=连接池耗尽
```

格式说明：
- 时间戳
- 模块名称
- 日志级别
- 日志消息

## 查看日志

### 实时查看日志文件
```bash
tail -f logs/aiops.log
```

### 查看最近的错误
```bash
grep ERROR logs/aiops.log | tail -20
```

### 查看特定用户的操作
```bash
grep "username=admin" logs/aiops.log
```

### 查看WebSocket活动
```bash
grep "WebSocket" logs/aiops.log
```

## 日志轮转

建议配置日志轮转以防止日志文件过大：

```python
# 在 logging_config.py 中添加 RotatingFileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
```

## 调试技巧

1. **开发环境**: 设置 `LOG_LEVEL=DEBUG` 查看详细信息
2. **生产环境**: 设置 `LOG_LEVEL=INFO` 或 `LOG_LEVEL=WARNING`
3. **排查问题**: 使用 `grep` 和 `tail` 过滤特定日志
4. **性能分析**: 关注 WARNING 级别的日志，可能指示性能问题
