from celery import Celery
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

celery_app = Celery(
    "aiops",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.diagnosis_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.celery_task_timeout,
    task_soft_time_limit=settings.celery_task_timeout - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

logger.info("Celery app initialized")
