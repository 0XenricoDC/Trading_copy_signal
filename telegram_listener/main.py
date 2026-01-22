"""Telegram listener for trading signals using Telethon."""

import asyncio
import logging
import os
import sys
from datetime import datetime

from telethon import TelegramClient, events
from telethon.sessions import StringSession
import redis.asyncio as redis

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.config import settings
from telegram_listener.handlers.signal_handler import SignalHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


class TelegramListener:
    """Main Telegram listener class."""

    def __init__(self):
        self.client: TelegramClient | None = None
        self.redis_client: redis.Redis | None = None
        self.signal_handler: SignalHandler | None = None
        self.monitored_channels: dict[int, dict] = {}  # channel_id -> channel info

    async def start(self):
        """Start the Telegram listener."""
        logger.info("Starting Telegram listener...")

        # Initialize Redis connection
        self.redis_client = redis.from_url(settings.REDIS_URL)

        # Initialize signal handler
        self.signal_handler = SignalHandler(self.redis_client)

        # Initialize Telegram client
        if settings.TELEGRAM_SESSION_STRING:
            session = StringSession(settings.TELEGRAM_SESSION_STRING)
        else:
            session = StringSession()

        if not settings.TELEGRAM_API_ID or not settings.TELEGRAM_API_HASH:
            raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")

        self.client = TelegramClient(
            session,
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
        )

        # Connect and start
        await self.client.start()

        # Load monitored channels from database
        await self.load_monitored_channels()

        # Register event handlers
        self.register_handlers()

        # If no session string, print it for saving
        if not settings.TELEGRAM_SESSION_STRING:
            logger.info(f"Session string: {self.client.session.save()}")
            logger.info("Save this session string to TELEGRAM_SESSION_STRING env var")

        logger.info("Telegram listener started successfully")

        # Start periodic tasks
        asyncio.create_task(self.periodic_channel_sync())

        # Keep running
        await self.client.run_until_disconnected()

    async def stop(self):
        """Stop the Telegram listener."""
        logger.info("Stopping Telegram listener...")

        if self.client:
            await self.client.disconnect()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Telegram listener stopped")

    async def load_monitored_channels(self):
        """Load monitored channels from database via Redis cache."""
        try:
            # Get channels from Redis (set by API)
            channels_json = await self.redis_client.get("telegram:monitored_channels")

            if channels_json:
                import json
                channels = json.loads(channels_json)
                self.monitored_channels = {
                    int(ch["channel_id"]): ch for ch in channels
                }
                logger.info(f"Loaded {len(self.monitored_channels)} monitored channels")
            else:
                logger.warning("No monitored channels found in Redis")

        except Exception as e:
            logger.error(f"Error loading monitored channels: {e}")

    async def periodic_channel_sync(self):
        """Periodically sync monitored channels from database."""
        while True:
            try:
                await asyncio.sleep(60)  # Sync every minute
                await self.load_monitored_channels()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic channel sync: {e}")

    def register_handlers(self):
        """Register Telegram event handlers."""

        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            """Handle new messages from monitored channels."""
            try:
                # Get chat ID
                chat_id = event.chat_id

                # Check if this channel is monitored
                if chat_id not in self.monitored_channels:
                    return

                channel_info = self.monitored_channels[chat_id]

                # Get message details
                message = event.message
                text = message.text or message.message or ""

                if not text.strip():
                    return

                logger.info(f"New message from {channel_info.get('channel_name', chat_id)}: {text[:100]}...")

                # Process the message
                await self.signal_handler.process_message(
                    channel_id=chat_id,
                    channel_info=channel_info,
                    message_id=message.id,
                    text=text,
                    timestamp=message.date,
                )

            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)

        @self.client.on(events.MessageEdited)
        async def handle_edited_message(event):
            """Handle edited messages (signal updates/corrections)."""
            try:
                chat_id = event.chat_id

                if chat_id not in self.monitored_channels:
                    return

                channel_info = self.monitored_channels[chat_id]
                message = event.message
                text = message.text or message.message or ""

                if not text.strip():
                    return

                logger.info(f"Edited message from {channel_info.get('channel_name', chat_id)}: {text[:100]}...")

                # Process as update
                await self.signal_handler.process_message_edit(
                    channel_id=chat_id,
                    channel_info=channel_info,
                    message_id=message.id,
                    text=text,
                    timestamp=message.date,
                )

            except Exception as e:
                logger.error(f"Error handling edited message: {e}", exc_info=True)


async def main():
    """Main entry point."""
    listener = TelegramListener()

    try:
        await listener.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await listener.stop()


if __name__ == "__main__":
    asyncio.run(main())
