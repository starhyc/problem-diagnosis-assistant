"""Deprecated investigation module.

Use `investigation_demo` and `investigation_control` for separated responsibilities.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.investigation_control import router as control_router
from app.api.v1.endpoints.investigation_demo import router as demo_router

router = APIRouter()
router.include_router(demo_router)
router.include_router(control_router)
