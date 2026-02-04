from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.logging_config import get_logger
from app.models.user import User
from app.schemas.user import TokenData
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)
security = HTTPBearer()
user_repo = UserRepository()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        logger.warning("Token验证失败: 无效的token")
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        logger.warning("Token验证失败: 缺少用户名")
        raise credentials_exception

    user = user_repo.get_by_username(username)
    if user is None:
        logger.warning(f"Token验证失败: 用户不存在 - {username}")
        raise credentials_exception

    if not user.is_active:
        logger.warning(f"Token验证失败: 用户已被禁用 - {username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    logger.debug(f"Token验证成功: username={username}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


def require_role(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(f"权限不足: user={current_user.username}, role={current_user.role}, required={allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return role_checker
