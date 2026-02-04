from fastapi import APIRouter
from app.api.v1.endpoints import auth, dashboard, investigation, knowledge, settings, websocket

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(investigation.router, prefix="/investigation", tags=["Investigation"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(websocket.router, tags=["WebSocket"])
