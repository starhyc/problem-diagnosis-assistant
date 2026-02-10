from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.middleware.permissions import admin_required
from app.schemas.user import UserResponse
from app.services.skill_loader import SkillLoader

router = APIRouter()
skill_loader = SkillLoader()


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
        return skill_loader.save_skill_package(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{skill_id}/enabled", response_model=dict)
def toggle_skill(skill_id: str, data: SkillToggleRequest, user: UserResponse = Depends(admin_required)):
    try:
        return skill_loader.set_enabled(skill_id, data.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{skill_id}/execute", response_model=dict)
def execute_skill(skill_id: str, data: SkillExecuteRequest, user: UserResponse = Depends(admin_required)):
    try:
        return skill_loader.execute_skill(skill_id, approval_granted=data.approval_granted)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
