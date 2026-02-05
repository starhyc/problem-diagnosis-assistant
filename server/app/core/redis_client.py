from redis import Redis
from redis.connection import ConnectionPool
from app.core.config import settings
from app.core.logging_config import get_logger
from typing import Optional

logger = get_logger(__name__)

class RedisClient:
    _instance: Optional['RedisClient'] = None
    _pool: Optional[ConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pool is None:
            self._pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=50,
                decode_responses=True
            )
            logger.info(f"Redis connection pool created: {settings.redis_url}")

    def get_client(self) -> Redis:
        """Get Redis client from pool"""
        return Redis(connection_pool=self._pool)

    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            client = self.get_client()
            client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

redis_client = RedisClient()
