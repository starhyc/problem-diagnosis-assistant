from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.roles import UserRole
from app.core.security import get_password_hash
from app.middleware.permissions import user_management_permission
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.services.settings_audit import SettingsAuditService

router = APIRouter()
user_repo = UserRepository()
audit_service = SettingsAuditService()


class AdminUserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str = Field(min_length=1, max_length=100)
    role: UserRole = Field(default=UserRole.VIEWER)


class UserStatusRequest(BaseModel):
    is_active: bool


class UserRoleRequest(BaseModel):
    role: UserRole


@router.get("/users", response_model=list[UserResponse])
def list_users(user: UserResponse = Depends(user_management_permission)):
    users = user_repo.get_all(limit=200)
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(data: AdminUserCreateRequest, user: UserResponse = Depends(user_management_permission)):
    if user_repo.username_exists(data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if user_repo.email_exists(data.email):
        raise HTTPException(status_code=400, detail="邮箱已存在")

    created = user_repo.create(
        username=data.username,
        email=data.email,
        display_name=data.display_name,
        hashed_password=get_password_hash(data.password),
        role=data.role.value,
        is_active=True,
    )

    audit_service.record(
        module="user-management",
        action="create",
        actor=user.username,
        target_id=created.username,
        detail={"role": created.role, "email": created.email},
    )
    return created


@router.put("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(user_id: int, data: UserStatusRequest, user: UserResponse = Depends(user_management_permission)):
    target = user_repo.get_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    updated = user_repo.update(user_id, is_active=data.is_active)
    audit_service.record(
        module="user-management",
        action="activate" if data.is_active else "disable",
        actor=user.username,
        target_id=target.username,
        detail={"is_active": data.is_active},
    )
    return updated


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(user_id: int, data: UserRoleRequest, user: UserResponse = Depends(user_management_permission)):
    target = user_repo.get_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    updated = user_repo.update(user_id, role=data.role.value)
    audit_service.record(
        module="user-management",
        action="change-role",
        actor=user.username,
        target_id=target.username,
        detail={"from": target.role, "to": data.role.value},
    )
    return updated

