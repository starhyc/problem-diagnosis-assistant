from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.logging_config import get_logger
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.api.deps import get_current_active_user
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)
router = APIRouter()
user_repo = UserRepository()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    logger.info(f"注册请求: username={user_data.username}, email={user_data.email}")

    if user_repo.username_exists(user_data.username):
        logger.warning(f"注册失败: 用户名已存在 - {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    if user_repo.email_exists(user_data.email):
        logger.warning(f"注册失败: 邮箱已被注册 - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    hashed_password = get_password_hash(user_data.password)
    new_user = user_repo.create(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        display_name=user_data.display_name,
        role=user_data.role
    )

    logger.info(f"用户注册成功: username={user_data.username}, role={user_data.role}")
    return new_user


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    logger.info(f"登录请求: username={user_data.username}")
    user = user_repo.get_by_username(user_data.username)

    if not user or not verify_password(user_data.password, user.hashed_password):
        logger.warning(f"登录失败: 账号或密码错误 - {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"登录失败: 用户已被禁用 - {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"登录成功: username={user_data.username}, role={user.role}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    logger.info(f"用户退出: username={current_user.username}")
    return {"message": "退出成功"}
