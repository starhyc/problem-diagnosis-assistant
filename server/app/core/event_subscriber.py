from typing import Callable, Dict, Any, Optional
import json
import asyncio
from app.core.redis_client import redis_client
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class EventSubscriber:
    def __init__(self):
        self.redis = redis_client.get_client()
        self.pubsub = None

    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to Redis Pub/Sub channel and process messages"""
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")

        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    try:
                        event = json.loads(message['data'])
                        await callback(event)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
        except Exception as e:
            logger.error(f"Subscription error: {e}")
        finally:
            if self.pubsub:
                self.pubsub.unsubscribe(channel)
                self.pubsub.close()

    def unsubscribe(self, channel: Optional[str] = None) -> None:
        """Unsubscribe from channel(s)"""
        if self.pubsub:
            if channel:
                self.pubsub.unsubscribe(channel)
            else:
                self.pubsub.unsubscribe()
            logger.info(f"Unsubscribed from channel: {channel or 'all'}")

event_subscriber = EventSubscriber()
