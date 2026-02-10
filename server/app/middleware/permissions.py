from fastapi import Depends, HTTPException, status
from app.api.deps import get_current_user
from app.schemas.user import UserResponse


def admin_required(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Dependency to require admin role for endpoint access"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def user_management_permission(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Permission gate for user lifecycle operations."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User management requires admin role"
        )
    return current_user
