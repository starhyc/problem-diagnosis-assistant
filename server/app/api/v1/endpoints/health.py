from fastapi import APIRouter, HTTPException
from app.core.celery_app import celery_app
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/celery")
async def health_check_celery():
    """Check Celery worker health"""
    try:
        # Check active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        stats = inspect.stats()

        if not active_workers:
            raise HTTPException(status_code=503, detail="No active Celery workers")

        return {
            "status": "healthy",
            "workers": list(active_workers.keys()),
            "worker_count": len(active_workers),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Celery unhealthy: {str(e)}")

@router.get("/celery/tasks")
async def get_task_stats():
    """Get Celery task statistics"""
    try:
        inspect = celery_app.control.inspect()

        return {
            "active": inspect.active(),
            "scheduled": inspect.scheduled(),
            "reserved": inspect.reserved(),
            "registered": inspect.registered()
        }
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
