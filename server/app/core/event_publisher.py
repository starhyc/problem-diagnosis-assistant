from typing import Dict, Any
import json
from app.core.redis_client import redis_client
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class EventPublisher:
    def __init__(self):
        self.redis = redis_client.get_client()

    def publish(self, channel: str, event: Dict[str, Any]) -> bool:
        """Publish event to Redis Pub/Sub channel"""
        try:
            message = json.dumps(event)
            self.redis.publish(channel, message)
            logger.debug(f"Published event to {channel}: {event.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to {channel}: {e}")
            return False

    def publish_diagnosis_event(self, session_id: str, event: Dict[str, Any]) -> bool:
        """Publish diagnosis event to session-specific channel"""
        channel = f"diagnosis:{session_id}"
        return self.publish(channel, event)

event_publisher = EventPublisher()
