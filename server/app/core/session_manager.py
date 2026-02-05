from typing import Optional, Dict, Any
import json
from datetime import datetime
from app.core.redis_client import redis_client
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class RedisSessionManager:
    def __init__(self):
        self.redis = redis_client.get_client()
        self.ttl = settings.redis_session_ttl

    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def create_session(self, session_id: str, user_id: str, diagnosis_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session in Redis"""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "diagnosis_id": diagnosis_id,
            "connected_at": datetime.now().isoformat(),
            "last_activity_at": datetime.now().isoformat()
        }
        key = self._session_key(session_id)
        self.redis.setex(key, self.ttl, json.dumps(session_data))
        logger.info(f"Session created: {session_id}")
        return session_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        key = self._session_key(session_id)
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data and refresh TTL"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.update(updates)
        session["last_activity_at"] = datetime.now().isoformat()

        key = self._session_key(session_id)
        self.redis.setex(key, self.ttl, json.dumps(session))
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        key = self._session_key(session_id)
        result = self.redis.delete(key)
        if result:
            logger.info(f"Session deleted: {session_id}")
        return bool(result)

    def refresh_ttl(self, session_id: str) -> bool:
        """Refresh session TTL"""
        key = self._session_key(session_id)
        return bool(self.redis.expire(key, self.ttl))

session_manager = RedisSessionManager()
