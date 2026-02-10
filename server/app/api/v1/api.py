from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    dashboard,
    investigation,
    history,
    knowledge,
    mcp_settings,
    settings_audit,
    settings,
    skills,
    user_management,
    websocket,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(investigation.router, prefix="/investigation", tags=["Investigation"])
api_router.include_router(history.router, prefix="/history", tags=["History"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(mcp_settings.router, prefix="/settings", tags=["MCP Settings"])
api_router.include_router(skills.router, prefix="/settings/skills", tags=["Skills"])
api_router.include_router(settings_audit.router, prefix="/settings", tags=["Settings Audit"])
api_router.include_router(user_management.router, prefix="/settings", tags=["User Management"])
api_router.include_router(websocket.router, tags=["WebSocket"])
