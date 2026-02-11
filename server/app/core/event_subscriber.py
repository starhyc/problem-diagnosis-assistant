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
        self._channel: Optional[str] = None
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None

    async def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to Redis Pub/Sub channel and process messages"""
        self._channel = channel
        self._running = True
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")

        try:
            while self._running:
                message = self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message:
                    await asyncio.sleep(0)
                    continue

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
            self._running = False
            if self.pubsub:
                try:
                    self.pubsub.unsubscribe(channel)
                except Exception as e:
                    logger.warning(f"Failed to unsubscribe from {channel}: {e}")
                try:
                    self.pubsub.close()
                except Exception as e:
                    logger.warning(f"Failed to close pubsub for {channel}: {e}")
                self.pubsub = None
            self._channel = None

    def unsubscribe(self, channel: Optional[str] = None) -> None:
        """Unsubscribe from channel(s)"""
        if self.pubsub:
            if channel:
                self.pubsub.unsubscribe(channel)
            else:
                self.pubsub.unsubscribe()
            logger.info(f"Unsubscribed from channel: {channel or 'all'}")

    async def subscribe_to_diagnosis(self, session_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to diagnosis event channel for a session."""
        if self._listen_task and not self._listen_task.done():
            return

        channel = f"diagnosis:{session_id}"
        self._listen_task = asyncio.create_task(self.subscribe(channel, callback))

    def stop(self) -> None:
        """Stop listening and close pubsub safely (idempotent)."""
        self._running = False

        if self.pubsub:
            try:
                if self._channel:
                    self.pubsub.unsubscribe(self._channel)
                else:
                    self.pubsub.unsubscribe()
            except Exception as e:
                logger.warning(f"Failed to unsubscribe during stop: {e}")

            try:
                self.pubsub.close()
            except Exception as e:
                logger.warning(f"Failed to close pubsub during stop: {e}")
            finally:
                self.pubsub = None

        self._channel = None

        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()

event_subscriber = EventSubscriber()
