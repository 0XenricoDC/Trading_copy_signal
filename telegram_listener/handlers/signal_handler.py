"""Signal handler for processing Telegram messages."""

import json
import logging
from datetime import datetime
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SignalHandler:
    """Handles processing of Telegram messages for trading signals."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def process_message(
        self,
        channel_id: int,
        channel_info: dict,
        message_id: int,
        text: str,
        timestamp: datetime,
    ):
        """Process a new message from Telegram.

        This publishes the raw message to Redis for the workers to process.
        """
        try:
            # Create message payload
            payload = {
                "type": "new_signal",
                "channel_id": channel_id,
                "channel_db_id": channel_info.get("id"),  # UUID from DB
                "tenant_id": channel_info.get("tenant_id"),
                "channel_name": channel_info.get("channel_name"),
                "message_id": message_id,
                "text": text,
                "timestamp": timestamp.isoformat(),
                "received_at": datetime.utcnow().isoformat(),
            }

            # Publish to Redis channel for workers
            await self.redis.publish(
                "telegram:signals",
                json.dumps(payload),
            )

            # Also queue for Celery processing
            await self.redis.rpush(
                "telegram:signal_queue",
                json.dumps(payload),
            )

            logger.info(f"Queued signal from channel {channel_id}, message {message_id}")

            # Store in recent messages for deduplication
            await self._store_recent_message(channel_id, message_id, text)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    async def process_message_edit(
        self,
        channel_id: int,
        channel_info: dict,
        message_id: int,
        text: str,
        timestamp: datetime,
    ):
        """Process an edited message from Telegram.

        This may update an existing signal or be a correction.
        """
        try:
            # Check if we processed the original message
            original_text = await self._get_recent_message(channel_id, message_id)

            if original_text and original_text != text:
                # Message was edited - publish update
                payload = {
                    "type": "signal_update",
                    "channel_id": channel_id,
                    "channel_db_id": channel_info.get("id"),
                    "tenant_id": channel_info.get("tenant_id"),
                    "channel_name": channel_info.get("channel_name"),
                    "message_id": message_id,
                    "text": text,
                    "original_text": original_text,
                    "timestamp": timestamp.isoformat(),
                    "received_at": datetime.utcnow().isoformat(),
                }

                await self.redis.publish(
                    "telegram:signals",
                    json.dumps(payload),
                )

                await self.redis.rpush(
                    "telegram:signal_queue",
                    json.dumps(payload),
                )

                logger.info(f"Queued signal update from channel {channel_id}, message {message_id}")

                # Update stored message
                await self._store_recent_message(channel_id, message_id, text)

        except Exception as e:
            logger.error(f"Error processing message edit: {e}", exc_info=True)

    async def _store_recent_message(self, channel_id: int, message_id: int, text: str):
        """Store recent message for deduplication."""
        key = f"telegram:messages:{channel_id}:{message_id}"
        await self.redis.setex(key, 86400, text)  # Expire after 24 hours

    async def _get_recent_message(self, channel_id: int, message_id: int) -> str | None:
        """Get a recently stored message."""
        key = f"telegram:messages:{channel_id}:{message_id}"
        result = await self.redis.get(key)
        return result.decode() if result else None
