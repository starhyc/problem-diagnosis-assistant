from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.middleware.permissions import admin_required
from app.schemas.user import UserResponse
from app.services.mcp_manager import MCPManager
from app.services.settings_audit import SettingsAuditService

router = APIRouter()
mcp_manager = MCPManager()
audit_service = SettingsAuditService()


class MCPServerRequest(BaseModel):
    id: str = Field(description="Unique server id")
    name: str
    transport: str = "http"
    endpoint: str
    enabled: bool = True
    version: str = "latest"


class MCPEnableRequest(BaseModel):
    enabled: bool


@router.get("/mcp-servers", response_model=list[dict])
def list_mcp_servers(user: UserResponse = Depends(admin_required)):
    rows = mcp_manager.list_servers()
    return [
        {
            "id": r.setting_id,
            "name": r.name,
            "transport": r.transport,
            "endpoint": r.endpoint,
            "enabled": r.enabled,
            "version": r.version,
            "status": r.status,
            "last_test_at": r.last_test_at,
            "last_test_status": r.last_test_status,
            "created_by": r.created_by,
            "updated_by": r.updated_by,
            "updated_at": r.updated_at,
        }
        for r in rows
    ]


@router.post("/mcp-servers", response_model=dict)
def upsert_mcp_server(data: MCPServerRequest, user: UserResponse = Depends(admin_required)):
    row = mcp_manager.upsert_server(
        setting_id=data.id,
        name=data.name,
        transport=data.transport,
        endpoint=data.endpoint,
        enabled=data.enabled,
        version=data.version,
        actor=user.username,
    )
    audit_service.record(
        module="mcp",
        action="upsert",
        actor=user.username,
        target_id=row.setting_id,
        detail={"enabled": row.enabled, "endpoint": row.endpoint},
    )
    return {
        "id": row.setting_id,
        "name": row.name,
        "transport": row.transport,
        "endpoint": row.endpoint,
        "enabled": row.enabled,
        "version": row.version,
        "status": row.status,
        "last_test_at": row.last_test_at,
        "last_test_status": row.last_test_status,
        "created_by": row.created_by,
        "updated_by": row.updated_by,
        "updated_at": row.updated_at,
    }


@router.put("/mcp-servers/{server_id}/enabled", response_model=dict)
def toggle_mcp_server(server_id: str, data: MCPEnableRequest, user: UserResponse = Depends(admin_required)):
    try:
        row = mcp_manager.set_enabled(server_id, data.enabled, actor=user.username)
        audit_service.record(
            module="mcp",
            action="enable" if data.enabled else "disable",
            actor=user.username,
            target_id=server_id,
            detail={"enabled": data.enabled},
        )
        return {
            "id": row.setting_id,
            "name": row.name,
            "transport": row.transport,
            "endpoint": row.endpoint,
            "enabled": row.enabled,
            "version": row.version,
            "status": row.status,
            "last_test_at": row.last_test_at,
            "last_test_status": row.last_test_status,
            "created_by": row.created_by,
            "updated_by": row.updated_by,
            "updated_at": row.updated_at,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/mcp-servers/{server_id}")
def delete_mcp_server(server_id: str, user: UserResponse = Depends(admin_required)):
    try:
        mcp_manager.delete_server(server_id)
        audit_service.record(
            module="mcp",
            action="delete",
            actor=user.username,
            target_id=server_id,
            detail={},
        )
        return {"status": "deleted"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/mcp-servers/{server_id}/test", response_model=dict)
def test_mcp_server(server_id: str, user: UserResponse = Depends(admin_required)):
    try:
        result = mcp_manager.test_connection(server_id)
        audit_service.record(
            module="mcp",
            action="test-connectivity",
            actor=user.username,
            target_id=server_id,
            detail=result,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
