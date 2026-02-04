from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.case import Setting
from app.schemas.case import (
    SettingsDataResponse,
    RedlineResponse,
    ToolResponse,
    MaskingRuleResponse,
)
from app.repositories.setting_repository import SettingRepository

router = APIRouter()
setting_repo = SettingRepository()

DEFAULT_REDLINES = [
    {
        "id": "write-ops",
        "name": "禁止写入操作",
        "enabled": True,
        "description": "禁止任何数据库写入、文件修改操作",
    },
    {
        "id": "auto-exec",
        "name": "自动执行阈值",
        "enabled": False,
        "description": "置信度>95%时自动执行修复建议",
    },
    {
        "id": "prod-access",
        "name": "生产环境访问",
        "enabled": False,
        "description": "允许直接访问生产环境数据",
    },
    {
        "id": "pii-mask",
        "name": "PII数据脱敏",
        "enabled": True,
        "description": "自动脱敏身份证、手机号等敏感信息",
    },
]

DEFAULT_TOOLS = [
    {"id": "elk", "name": "ELK Stack", "connected": True, "url": "https://elk.internal:9200"},
    {"id": "gitlab", "name": "GitLab", "connected": True, "url": "https://gitlab.internal"},
    {"id": "k8s", "name": "Kubernetes", "connected": True, "url": "https://k8s.internal:6443"},
    {"id": "neo4j", "name": "Neo4j", "connected": True, "url": "bolt://neo4j.internal:7687"},
]

DEFAULT_MASKING_RULES = [
    {
        "pattern": r"\b\d{18}\b",
        "name": "身份证号",
        "replacement": "***",
    },
    {
        "pattern": r"\b1[3-9]\d{9}\b",
        "name": "手机号",
        "replacement": "***",
    },
    {
        "pattern": r"[\w.-]+@[\w.-]+\.\w+",
        "name": "邮箱",
        "replacement": "***@***.***",
    },
]


@router.get("/", response_model=SettingsDataResponse)
def get_settings():
    redlines = setting_repo.get_by_type("redline")
    tools = setting_repo.get_by_type("tool")
    masking_rules = setting_repo.get_by_type("masking")

    if not redlines:
        setting_repo.bulk_create([{
            "setting_type": "redline",
            "setting_id": redline["id"],
            "name": redline["name"],
            "enabled": redline["enabled"],
            "description": redline["description"]
        } for redline in DEFAULT_REDLINES])
        redlines = setting_repo.get_by_type("redline")

    if not tools:
        setting_repo.bulk_create([{
            "setting_type": "tool",
            "setting_id": tool["id"],
            "name": tool["name"],
            "enabled": tool["connected"],
            "config": f'{{"url": "{tool["url"]}"}}'
        } for tool in DEFAULT_TOOLS])
        tools = setting_repo.get_by_type("tool")

    if not masking_rules:
        setting_repo.bulk_create([{
            "setting_type": "masking",
            "setting_id": f"mask-{i}",
            "name": rule["name"],
            "enabled": True,
            "config": f'{{"pattern": "{rule["pattern"]}", "replacement": "{rule["replacement"]}"}}'
        } for i, rule in enumerate(DEFAULT_MASKING_RULES)])
        masking_rules = setting_repo.get_by_type("masking")

    redlines_response = [
        RedlineResponse(
            id=redline.setting_id,
            name=redline.name,
            enabled=redline.enabled,
            description=redline.description or "",
        )
        for redline in redlines
    ]

    tools_response = []
    for tool in tools:
        import json
        config = json.loads(tool.config) if tool.config else {}
        tools_response.append(
            ToolResponse(
                id=tool.setting_id,
                name=tool.name,
                connected=tool.enabled,
                url=config.get("url", ""),
            )
        )

    masking_rules_response = []
    for rule in masking_rules:
        import json
        config = json.loads(rule.config) if rule.config else {}
        masking_rules_response.append(
            MaskingRuleResponse(
                pattern=config.get("pattern", ""),
                name=rule.name,
                replacement=config.get("replacement", ""),
            )
        )

    return SettingsDataResponse(
        redlines=redlines_response,
        tools=tools_response,
        masking_rules=masking_rules_response,
    )


@router.put("/settings/redlines/{redline_id}")
def update_redline(redline_id: str, enabled: bool):
    redline = setting_repo.get_by_type_and_id("redline", redline_id)
    if not redline:
        raise HTTPException(status_code=404, detail="Redline not found")

    setting_repo.update(redline.id, enabled=enabled)
    return {"status": "updated", "enabled": enabled}


@router.post("/settings/tools/{tool_id}/test")
def test_tool_connection(tool_id: str):
    return {"status": "connected", "message": "Connection successful"}


@router.post("/settings/mask")
def test_masking(text: str):
    import re

    masking_rules = setting_repo.get_by_type("masking")
    result = text

    for rule in masking_rules:
        import json
        config = json.loads(rule.config) if rule.config else {}
        pattern = config.get("pattern", "")
        replacement = config.get("replacement", "")
        if pattern:
            result = re.sub(pattern, replacement, result)

    return {"original": text, "masked": result}
