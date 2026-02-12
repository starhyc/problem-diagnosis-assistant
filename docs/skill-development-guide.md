# Skill 开发指南

## 1. Skill 概述

### 1.1 什么是 Skill

Skill 是智能问题定位 Agent 系统中的可插拔能力单元，封装了特定领域的问题排查知识和执行逻辑。每个 Skill 定义了：

- 问题识别规则（何时触发）
- 排查步骤（如何执行）
- 依赖的工具和知识库
- 输入/输出规范

### 1.2 Skill 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Skill 架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Skill Metadata                        │   │
│  │  • skill_id, name, version                               │   │
│  │  • domain, tags, description                             │   │
│  │  • input_schema, output_schema                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────┼───────────────────────────┐     │
│  │                           │                           │     │
│  │  ┌─────────────┐    ┌─────┴─────┐    ┌─────────────┐ │     │
│  │  │  Triggers   │    │Execution  │    │Dependencies │ │     │
│  │  │  触发规则   │    │  Logic    │    │   依赖配置  │ │     │
│  │  └─────────────┘    │  执行逻辑 │    └─────────────┘ │     │
│  │                     └───────────┘                      │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Skill 定义规范

### 2.1 元数据结构

```python
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum

class SkillStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    PENDING = "pending"
    FAILED = "failed"

class SkillMetadata(BaseModel):
    skill_id: str = Field(..., description="Skill 唯一标识")
    name: str = Field(..., description="Skill 名称")
    version: str = Field(default="1.0.0", description="版本号")
    domain: str = Field(..., description="所属领域")
    description: str = Field(..., description="功能描述")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    
    input_schema: Dict[str, Any] = Field(..., description="输入参数 Schema")
    output_schema: Dict[str, Any] = Field(..., description="输出结果 Schema")
    
    dependencies: Dict[str, List[str]] = Field(
        default_factory=lambda: {"tools": [], "skills": [], "knowledge_bases": []},
        description="依赖配置"
    )
    
    triggers: Dict[str, Any] = Field(
        default_factory=lambda: {"keywords": [], "patterns": [], "events": []},
        description="触发规则"
    )
    
    execution_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timeout": 60,
            "retry_policy": {"max_retries": 2, "backoff": "exponential"},
            "resource_limits": {"memory": "512MB", "cpu": "1"}
        },
        description="执行配置"
    )
    
    status: SkillStatus = Field(default=SkillStatus.ACTIVE, description="状态")
```

### 2.2 Skill 基类

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict, Optional
import asyncio

class BaseSkill(ABC):
    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
        self._tools = {}
        self._knowledge_bases = {}
    
    @property
    def skill_id(self) -> str:
        return self.metadata.skill_id
    
    @property
    def name(self) -> str:
        return self.metadata.name
    
    def register_tool(self, tool_name: str, tool_instance: Any):
        self._tools[tool_name] = tool_instance
    
    def register_knowledge_base(self, kb_name: str, kb_instance: Any):
        self._knowledge_bases[kb_name] = kb_instance
    
    @abstractmethod
    async def execute(
        self, 
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass
    
    async def validate_input(self, params: Dict[str, Any]) -> bool:
        pass
    
    def should_trigger(self, user_input: str, context: Dict[str, Any]) -> float:
        pass
```

## 3. Skill 开发示例

### 3.1 完整 Skill 示例：K8s Pod 崩溃分析

```python
import re
from typing import AsyncGenerator, Dict, Any, Optional
from backend.app.skills.base import BaseSkill, SkillMetadata, SkillStatus

class K8sPodCrashAnalysisSkill(BaseSkill):
    def __init__(self):
        metadata = SkillMetadata(
            skill_id="k8s-pod-crash-analysis",
            name="K8s Pod 崩溃分析",
            version="1.2.0",
            domain="kubernetes",
            description="分析 Kubernetes Pod 崩溃原因，包括 OOM、镜像拉取失败等",
            tags=["k8s", "pod", "crash", "oom", "troubleshooting"],
            
            input_schema={
                "type": "object",
                "required": ["pod_name", "namespace"],
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": "Pod 名称"
                    },
                    "namespace": {
                        "type": "string",
                        "default": "default",
                        "description": "命名空间"
                    },
                    "time_range": {
                        "type": "string",
                        "default": "1h",
                        "description": "时间范围"
                    },
                    "log_lines": {
                        "type": "integer",
                        "default": 500,
                        "description": "日志行数"
                    }
                }
            },
            
            output_schema={
                "type": "object",
                "properties": {
                    "root_cause": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "recommendations": {"type": "array"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            },
            
            dependencies={
                "tools": ["kubectl", "log-parser", "prometheus-query"],
                "skills": ["log-pattern-matching"],
                "knowledge_bases": ["k8s-error-codes", "k8s-best-practices"]
            },
            
            triggers={
                "keywords": ["pod crash", "container terminated", "OOMKilled", "pod restart"],
                "patterns": [
                    r"pod\s+\S+\s+(crash|restart|terminated)",
                    r"container\s+\S+\s+exited",
                    r"OOMKilled"
                ],
                "events": ["k8s.pod.crash", "k8s.container.oom"]
            },
            
            execution_config={
                "timeout": 120,
                "retry_policy": {
                    "max_retries": 2,
                    "backoff": "exponential"
                },
                "resource_limits": {
                    "memory": "512MB",
                    "cpu": "1"
                }
            },
            
            status=SkillStatus.ACTIVE
        )
        
        super().__init__(metadata)
    
    def should_trigger(self, user_input: str, context: Dict[str, Any]) -> float:
        score = 0.0
        
        keywords = self.metadata.triggers.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in user_input.lower():
                score += 0.2
        
        patterns = self.metadata.triggers.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                score += 0.3
        
        if context.get("domain") == "kubernetes":
            score += 0.2
        
        return min(score, 1.0)
    
    async def validate_input(self, params: Dict[str, Any]) -> bool:
        required = self.metadata.input_schema.get("required", [])
        return all(param in params for param in required)
    
    async def execute(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pod_name = params["pod_name"]
        namespace = params.get("namespace", "default")
        time_range = params.get("time_range", "1h")
        
        yield {
            "type": "progress",
            "message": f"开始分析 Pod {pod_name} 的崩溃原因..."
        }
        
        yield {
            "type": "progress",
            "message": "获取 Pod 状态信息..."
        }
        pod_status = await self._get_pod_status(pod_name, namespace)
        yield {
            "type": "tool_result",
            "tool": "kubectl_describe_pod",
            "result": pod_status
        }
        
        if pod_status.get("state") == "OOMKilled":
            yield {
                "type": "progress",
                "message": "检测到 OOMKilled，分析内存使用情况..."
            }
            result = await self._analyze_oom(pod_name, namespace, pod_status)
            yield result
            return
        
        yield {
            "type": "progress",
            "message": "获取容器日志..."
        }
        logs = await self._get_pod_logs(pod_name, namespace, params.get("log_lines", 500))
        yield {
            "type": "tool_result",
            "tool": "kubectl_logs",
            "result": {"log_count": len(logs.split("\n"))}
        }
        
        yield {
            "type": "progress",
            "message": "分析日志模式..."
        }
        log_analysis = await self._analyze_logs(logs)
        
        yield {
            "type": "progress",
            "message": "检索相关知识..."
        }
        knowledge = await self._search_knowledge(log_analysis)
        
        final_result = self._generate_result(pod_status, log_analysis, knowledge)
        yield final_result
    
    async def _get_pod_status(self, pod_name: str, namespace: str) -> Dict[str, Any]:
        kubectl = self._tools.get("kubectl")
        result = await kubectl.execute(
            command="describe",
            resource_type="pod",
            name=pod_name,
            namespace=namespace
        )
        
        status = {
            "name": pod_name,
            "namespace": namespace,
            "state": "unknown",
            "restart_count": 0,
            "last_state": None,
            "events": []
        }
        
        if "OOMKilled" in result:
            status["state"] = "OOMKilled"
        elif "CrashLoopBackOff" in result:
            status["state"] = "CrashLoopBackOff"
        elif "ImagePullBackOff" in result:
            status["state"] = "ImagePullBackOff"
        
        return status
    
    async def _get_pod_logs(self, pod_name: str, namespace: str, lines: int) -> str:
        kubectl = self._tools.get("kubectl")
        return await kubectl.execute(
            command="logs",
            resource_type="pod",
            name=pod_name,
            namespace=namespace,
            tail=lines,
            previous=True
        )
    
    async def _analyze_logs(self, logs: str) -> Dict[str, Any]:
        log_parser = self._tools.get("log-parser")
        
        error_patterns = [
            r"ERROR",
            r"FATAL",
            r"Exception",
            r"OutOfMemory",
            r"timeout",
            r"connection refused"
        ]
        
        analysis = {
            "error_count": 0,
            "error_types": {},
            "last_errors": [],
            "patterns_found": []
        }
        
        for pattern in error_patterns:
            matches = re.findall(pattern, logs, re.IGNORECASE)
            if matches:
                analysis["error_types"][pattern] = len(matches)
                analysis["error_count"] += len(matches)
        
        lines = logs.split("\n")
        analysis["last_errors"] = [
            line for line in lines[-50:]
            if any(re.search(p, line, re.IGNORECASE) for p in error_patterns)
        ][:5]
        
        return analysis
    
    async def _analyze_oom(
        self, 
        pod_name: str, 
        namespace: str,
        pod_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        prometheus = self._tools.get("prometheus-query")
        
        memory_query = f'container_memory_usage_bytes{{pod="{pod_name}",namespace="{namespace}"}}'
        memory_data = await prometheus.query(memory_query, time_range="1h")
        
        kb = self._knowledge_bases.get("k8s-best-practices")
        oom_guide = await kb.search("kubernetes oom troubleshooting")
        
        return {
            "type": "final_result",
            "root_cause": "容器内存不足，触发 OOMKilled",
            "evidence": [
                f"Pod 状态: {pod_status['state']}",
                f"内存使用峰值: {memory_data.get('max', 'N/A')}",
                "容器被 OOM Killer 终止"
            ],
            "recommendations": [
                "增加容器内存限制 (当前可能过低)",
                "检查应用是否存在内存泄漏",
                "优化应用内存使用",
                "考虑启用内存限制的垂直扩展"
            ],
            "confidence": 0.92,
            "related_docs": oom_guide[:3] if oom_guide else []
        }
    
    async def _search_knowledge(self, log_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        kb = self._knowledge_bases.get("k8s-error-codes")
        if not kb:
            return []
        
        queries = []
        for error_type in log_analysis.get("error_types", {}).keys():
            queries.append(f"kubernetes {error_type} troubleshooting")
        
        results = []
        for query in queries[:3]:
            docs = await kb.search(query, top_k=2)
            results.extend(docs)
        
        return results
    
    def _generate_result(
        self,
        pod_status: Dict[str, Any],
        log_analysis: Dict[str, Any],
        knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        root_cause = self._determine_root_cause(pod_status, log_analysis)
        confidence = self._calculate_confidence(pod_status, log_analysis)
        
        return {
            "type": "final_result",
            "root_cause": root_cause,
            "evidence": self._extract_evidence(pod_status, log_analysis),
            "recommendations": self._generate_recommendations(root_cause, knowledge),
            "confidence": confidence,
            "related_docs": knowledge[:3]
        }
    
    def _determine_root_cause(
        self, 
        pod_status: Dict[str, Any], 
        log_analysis: Dict[str, Any]
    ) -> str:
        if pod_status["state"] == "OOMKilled":
            return "容器内存限制过低，触发 OOM Killer"
        elif pod_status["state"] == "ImagePullBackOff":
            return "容器镜像拉取失败"
        elif pod_status["state"] == "CrashLoopBackOff":
            if "OutOfMemory" in str(log_analysis.get("error_types", {})):
                return "应用内存溢出导致崩溃"
            elif "connection refused" in str(log_analysis.get("error_types", {})):
                return "应用无法连接依赖服务"
            else:
                return "应用启动失败，需要进一步分析日志"
        else:
            return "需要更多信息来确定根因"
    
    def _calculate_confidence(
        self, 
        pod_status: Dict[str, Any], 
        log_analysis: Dict[str, Any]
    ) -> float:
        confidence = 0.5
        
        if pod_status["state"] != "unknown":
            confidence += 0.2
        
        if log_analysis.get("error_count", 0) > 0:
            confidence += 0.1
        
        if log_analysis.get("last_errors"):
            confidence += 0.1
        
        if pod_status["state"] in ["OOMKilled", "ImagePullBackOff"]:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_evidence(
        self, 
        pod_status: Dict[str, Any], 
        log_analysis: Dict[str, Any]
    ) -> List[str]:
        evidence = []
        
        if pod_status["state"] != "unknown":
            evidence.append(f"Pod 状态: {pod_status['state']}")
        
        if pod_status.get("restart_count", 0) > 0:
            evidence.append(f"重启次数: {pod_status['restart_count']}")
        
        for error_type, count in log_analysis.get("error_types", {}).items():
            evidence.append(f"发现 {count} 次 {error_type} 错误")
        
        for error in log_analysis.get("last_errors", [])[:3]:
            evidence.append(f"最近错误: {error[:100]}...")
        
        return evidence
    
    def _generate_recommendations(
        self, 
        root_cause: str, 
        knowledge: List[Dict[str, Any]]
    ) -> List[str]:
        recommendations = []
        
        if "OOM" in root_cause or "内存" in root_cause:
            recommendations.extend([
                "增加容器内存限制",
                "检查应用是否存在内存泄漏",
                "优化 JVM 堆内存配置（如适用）"
            ])
        elif "镜像" in root_cause:
            recommendations.extend([
                "检查镜像名称和标签是否正确",
                "验证镜像仓库访问权限",
                "检查网络连接"
            ])
        elif "连接" in root_cause:
            recommendations.extend([
                "检查依赖服务状态",
                "验证网络策略配置",
                "检查服务发现配置"
            ])
        
        for doc in knowledge[:2]:
            if doc.get("recommendation"):
                recommendations.append(doc["recommendation"])
        
        return recommendations
```

### 3.2 Skill 注册

```python
from backend.app.skills.registry import SkillRegistry

registry = SkillRegistry()

skill = K8sPodCrashAnalysisSkill()
registry.register(skill)
```

## 4. Skill 生命周期

### 4.1 注册流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ 创建     │────►│ 验证     │────►│ 加载     │────►│ 激活     │
│ Skill    │     │ Schema   │     │ 依赖     │     │ 上线     │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### 4.2 版本管理

```python
class SkillVersion:
    def __init__(self, skill_id: str, versions: List[str]):
        self.skill_id = skill_id
        self.versions = versions
        self.active_version = versions[-1]
    
    def promote(self, version: str):
        if version in self.versions:
            self.active_version = version
    
    def deprecate(self, version: str):
        pass
    
    def rollback(self):
        current_idx = self.versions.index(self.active_version)
        if current_idx > 0:
            self.active_version = self.versions[current_idx - 1]
```

## 5. Skill 测试

### 5.1 单元测试

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def skill():
    return K8sPodCrashAnalysisSkill()

@pytest.fixture
def mock_tools():
    return {
        "kubectl": AsyncMock(),
        "log-parser": AsyncMock(),
        "prometheus-query": AsyncMock()
    }

@pytest.mark.asyncio
async def test_should_trigger(skill):
    assert skill.should_trigger("我的 Pod 一直重启", {}) > 0.5
    assert skill.should_trigger("Pod OOMKilled", {}) > 0.5
    assert skill.should_trigger("数据库连接问题", {}) < 0.3

@pytest.mark.asyncio
async def test_execute_oom_case(skill, mock_tools):
    skill._tools = mock_tools
    
    mock_tools["kubectl"].execute.return_value = "OOMKilled"
    mock_tools["prometheus-query"].query.return_value = {"max": "512Mi"}
    
    results = []
    async for result in skill.execute({
        "pod_name": "test-pod",
        "namespace": "default"
    }):
        results.append(result)
    
    final_result = results[-1]
    assert final_result["type"] == "final_result"
    assert "OOM" in final_result["root_cause"]
    assert final_result["confidence"] > 0.8
```

### 5.2 集成测试

```python
@pytest.mark.integration
async def test_skill_end_to_end():
    registry = SkillRegistry()
    skill = K8sPodCrashAnalysisSkill()
    registry.register(skill)
    
    retrieved = registry.get("k8s-pod-crash-analysis")
    assert retrieved is not None
    assert retrieved.skill_id == "k8s-pod-crash-analysis"
```

## 6. Skill 最佳实践

### 6.1 命名规范

- skill_id: `{domain}-{problem-type}-{action}`
- 示例: `k8s-pod-crash-analysis`, `mysql-slow-query-optimization`

### 6.2 输入验证

```python
async def validate_input(self, params: Dict[str, Any]) -> bool:
    schema = self.metadata.input_schema
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    
    for field in required:
        if field not in params:
            raise ValidationError(f"Missing required field: {field}")
    
    for field, value in params.items():
        if field in properties:
            field_schema = properties[field]
            if field_schema.get("type") == "string":
                if not isinstance(value, str):
                    raise ValidationError(f"Field {field} must be string")
            elif field_schema.get("type") == "integer":
                if not isinstance(value, int):
                    raise ValidationError(f"Field {field} must be integer")
    
    return True
```

### 6.3 错误处理

```python
async def execute(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
    try:
        yield {"type": "progress", "message": "开始执行..."}
        
        result = await self._do_work(params)
        yield result
        
    except ToolExecutionError as e:
        yield {
            "type": "error",
            "error_type": "tool_execution_failed",
            "message": str(e),
            "recoverable": True
        }
    
    except ValidationError as e:
        yield {
            "type": "error",
            "error_type": "validation_failed",
            "message": str(e),
            "recoverable": False
        }
    
    except Exception as e:
        yield {
            "type": "error",
            "error_type": "unexpected_error",
            "message": str(e),
            "recoverable": False
        }
```

### 6.4 性能优化

```python
class CachedSkill(BaseSkill):
    def __init__(self, metadata: SkillMetadata, cache_ttl: int = 300):
        super().__init__(metadata)
        self._cache = {}
        self._cache_ttl = cache_ttl
    
    def _cache_key(self, params: Dict[str, Any]) -> str:
        import hashlib
        import json
        return hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
    
    async def execute(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
        cache_key = self._cache_key(params)
        
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                yield cached_result
                return
        
        async for result in self._execute_internal(params, context):
            if result.get("type") == "final_result":
                self._cache[cache_key] = (result, time.time())
            yield result
```

## 7. Skill 发布流程

### 7.1 发布检查清单

- [ ] 元数据完整且符合规范
- [ ] 输入/输出 Schema 正确定义
- [ ] 依赖工具和知识库已配置
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 文档完整
- [ ] 性能测试通过

### 7.2 发布命令

```bash
# 注册 Skill
python scripts/register_skill.py --skill-path skills/kubernetes/pod_crash.py

# 验证 Skill
python scripts/validate_skill.py --skill-id k8s-pod-crash-analysis

# 发布 Skill
python scripts/publish_skill.py --skill-id k8s-pod-crash-analysis --version 1.2.0
```
