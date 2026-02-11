import pytest
from fastapi import HTTPException
from datetime import datetime

from pydantic import ValidationError

from app.core.config import Settings
from app.middleware.permissions import admin_required
from app.schemas.user import UserCreate, UserResponse


def _base_settings_kwargs():
    return {
        "secret_key": "x" * 32,
        "database_url": "postgresql://user:pass@localhost:5432/aiops",
        "redis_url": "redis://localhost:6379/0",
        "cors_origins": "http://localhost:3000",
    }


def test_debug_defaults_to_false():
    settings = Settings(_env_file=None, **_base_settings_kwargs())
    assert settings.debug is False


def test_production_requires_secret_key():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            environment="production",
            secret_key=None,
            database_url="postgresql://user:pass@localhost:5432/aiops",
            redis_url="redis://localhost:6379/0",
            cors_origins="http://localhost:3000",
        )


def test_invalid_database_url_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**_base_settings_kwargs(), "database_url": "mysql://localhost/test"})


def test_invalid_redis_url_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**_base_settings_kwargs(), "redis_url": "http://localhost:6379"})


def test_invalid_cors_origin_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**_base_settings_kwargs(), "cors_origins": "localhost:3000"})


def test_user_create_rejects_invalid_role():
    with pytest.raises(ValidationError):
        UserCreate(
            username="test_user",
            email="test@example.com",
            display_name="Test",
            role="super_admin",
            password="secure_password",
        )


def test_admin_permission_rejects_illegal_role():
    user = UserResponse.model_construct(
        id=1,
        username="bad_role_user",
        email="bad-role@example.com",
        display_name="Bad Role",
        role="super_admin",
        is_active=True,
        created_at=datetime.utcnow(),
    )

    with pytest.raises(HTTPException) as exc:
        admin_required(user)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Invalid user role"
