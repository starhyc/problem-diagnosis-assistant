from fastapi import APIRouter, Depends, Query

from app.middleware.permissions import admin_required
from app.schemas.user import UserResponse
from app.services.settings_audit import SettingsAuditService

router = APIRouter()
audit_service = SettingsAuditService()


@router.get("/modules/{module}/audit-logs", response_model=list[dict])
def get_module_audit_logs(
    module: str,
    limit: int = Query(default=20, ge=1, le=100),
    session_id: str | None = Query(default=None),
    user: UserResponse = Depends(admin_required),
):
    return audit_service.list_recent(module=module, limit=limit, session_id=session_id)


@router.get("/modules/{module}/recent-changes", response_model=list[dict])
def get_module_recent_changes(
    module: str,
    limit: int = Query(default=5, ge=1, le=50),
    session_id: str | None = Query(default=None),
    user: UserResponse = Depends(admin_required),
):
    return audit_service.list_recent(module=module, limit=limit, session_id=session_id)



@router.get("/audit/session/{session_id}", response_model=list[dict])
def get_audit_by_session_id(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    user: UserResponse = Depends(admin_required),
):
    return audit_service.list_by_session_id(session_id=session_id, limit=limit)
