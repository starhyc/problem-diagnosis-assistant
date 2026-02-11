from typing import Dict, Any
import json
from app.core.redis_client import redis_client
from app.core.logging_config import get_logger
from app.contracts.diagnosis_protocol import InvalidDiagnosisEvent, normalize_event

logger = get_logger(__name__)

class EventPublisher:
    def __init__(self):
        self.redis = redis_client.get_client()

    def publish(self, channel: str, event: Dict[str, Any]) -> bool:
        """Publish event to Redis Pub/Sub channel"""
        try:
            validated_event = normalize_event(event)
            message = json.dumps(validated_event)
            self.redis.publish(channel, message)
            logger.debug(f"Published event to {channel}: {validated_event.get('type', 'unknown')}")
            return True
        except InvalidDiagnosisEvent as e:
            logger.warning(f"Refused to publish event to {channel}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to publish event to {channel}: {e}")
            return False

    def publish_diagnosis_event(self, session_id: str, event: Dict[str, Any]) -> bool:
        """Publish diagnosis event to session-specific channel"""
        channel = f"diagnosis:{session_id}"
        return self.publish(channel, event)

event_publisher = EventPublisher()
