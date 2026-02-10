from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.middleware.permissions import admin_required
from app.schemas.user import UserResponse
from app.services.skill_loader import SkillLoader
from app.services.settings_audit import SettingsAuditService

router = APIRouter()
skill_loader = SkillLoader()
audit_service = SettingsAuditService()


class SkillToggleRequest(BaseModel):
    enabled: bool


class SkillExecuteRequest(BaseModel):
    approval_granted: bool = False


@router.get("", response_model=list[dict])
def list_skills(user: UserResponse = Depends(admin_required)):
    return skill_loader.list_skills()


@router.post("/upload", response_model=dict)
async def upload_skill(
    file: UploadFile = File(...),
    user: UserResponse = Depends(admin_required),
):
    try:
        content = await file.read()
        saved = skill_loader.save_skill_package(file.filename, content, actor=user.username)
        audit_service.record(
            module="skill",
            action="upload",
            actor=user.username,
            target_id=saved["id"],
            detail={"filename": file.filename, "version": saved.get("version")},
        )
        return saved
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{skill_id}/enabled", response_model=dict)
def toggle_skill(skill_id: str, data: SkillToggleRequest, user: UserResponse = Depends(admin_required)):
    try:
        updated = skill_loader.set_enabled(skill_id, data.enabled, actor=user.username)
        audit_service.record(
            module="skill",
            action="enable" if data.enabled else "disable",
            actor=user.username,
            target_id=skill_id,
            detail={"enabled": data.enabled},
        )
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{skill_id}/execute", response_model=dict)
def execute_skill(skill_id: str, data: SkillExecuteRequest, user: UserResponse = Depends(admin_required)):
    try:
        result = skill_loader.execute_skill(skill_id, approval_granted=data.approval_granted)
        audit_service.record(
            module="skill",
            action="execute",
            actor=user.username,
            target_id=skill_id,
            detail={"status": result.get("status", "done"), "returncode": result.get("returncode")},
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{skill_id}/test", response_model=dict)
def test_skill(skill_id: str, user: UserResponse = Depends(admin_required)):
    try:
        result = skill_loader.test_skill(skill_id)
        audit_service.record(
            module="skill",
            action="test-connectivity",
            actor=user.username,
            target_id=skill_id,
            detail=result,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
