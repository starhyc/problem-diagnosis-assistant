from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.middleware.permissions import admin_required
from app.schemas.user import UserResponse
from app.services.mcp_manager import MCPManager

router = APIRouter()
mcp_manager = MCPManager()


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
    )
    return {
        "id": row.setting_id,
        "name": row.name,
        "transport": row.transport,
        "endpoint": row.endpoint,
        "enabled": row.enabled,
        "version": row.version,
    }


@router.put("/mcp-servers/{server_id}/enabled", response_model=dict)
def toggle_mcp_server(server_id: str, data: MCPEnableRequest, user: UserResponse = Depends(admin_required)):
    try:
        row = mcp_manager.set_enabled(server_id, data.enabled)
        return {
            "id": row.setting_id,
            "name": row.name,
            "transport": row.transport,
            "endpoint": row.endpoint,
            "enabled": row.enabled,
            "version": row.version,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/mcp-servers/{server_id}")
def delete_mcp_server(server_id: str, user: UserResponse = Depends(admin_required)):
    try:
        mcp_manager.delete_server(server_id)
        return {"status": "deleted"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/mcp-servers/{server_id}/test", response_model=dict)
def test_mcp_server(server_id: str, user: UserResponse = Depends(admin_required)):
    try:
        return mcp_manager.test_connection(server_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
