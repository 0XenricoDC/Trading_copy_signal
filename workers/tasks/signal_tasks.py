"""Signal processing tasks."""

import json
import logging
from datetime import datetime, timedelta
from uuid import UUID

from celery import shared_task
from sqlalchemy import select, and_

from workers.celery_app import app
from workers.parsers.regex_parser import SignalParser
from backend.app.db.session import async_session_maker
from backend.app.models.signal import RawSignal, ParsedSignal, SourceType, SignalStatus
from backend.app.models.subscription import SignalSubscription
from backend.app.models.trade import Trade, TradeStatus
from backend.app.models.telegram_channel import TelegramChannel

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_signal(
    self,
    signal_id: str,
    subscription_ids: list[str] | None = None,
) -> dict:
    """Process a parsed signal and create trades.

    Args:
        signal_id: UUID of the parsed signal
        subscription_ids: Optional list of subscription IDs to process (all active if None)

    Returns:
        dict with processing result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _process_signal_async(self, signal_id, subscription_ids)
    )


async def _process_signal_async(
    task,
    signal_id: str,
    subscription_ids: list[str] | None,
) -> dict:
    """Async implementation of signal processing."""
    async with async_session_maker() as db:
        try:
            # Get signal
            result = await db.execute(
                select(ParsedSignal).where(ParsedSignal.id == UUID(signal_id))
            )
            signal = result.scalar_one_or_none()

            if not signal:
                return {"success": False, "error": "Signal not found"}

            if signal.status not in [SignalStatus.PENDING, SignalStatus.PROCESSING]:
                return {"success": False, "error": f"Signal in invalid status: {signal.status}"}

            # Update status
            signal.status = SignalStatus.PROCESSING
            await db.commit()

            # Get subscriptions
            query = select(SignalSubscription).where(
                SignalSubscription.tenant_id == signal.tenant_id,
                SignalSubscription.is_active == True,
            )

            if subscription_ids:
                query = query.where(
                    SignalSubscription.id.in_([UUID(sid) for sid in subscription_ids])
                )

            # If signal came from a channel, filter to subscriptions for that channel
            if signal.raw_signal_id:
                raw_result = await db.execute(
                    select(RawSignal).where(RawSignal.id == signal.raw_signal_id)
                )
                raw_signal = raw_result.scalar_one_or_none()
                if raw_signal and raw_signal.channel_id:
                    query = query.where(
                        SignalSubscription.channel_id == raw_signal.channel_id
                    )

            result = await db.execute(query)
            subscriptions = result.scalars().all()

            if not subscriptions:
                signal.status = SignalStatus.FAILED
                signal.error_message = "No active subscriptions found"
                await db.commit()
                return {"success": False, "error": "No active subscriptions found"}

            # Create trades for each subscription
            trades_created = 0
            trades_failed = 0

            for subscription in subscriptions:
                try:
                    # Check symbol filter
                    if not _check_symbol_filter(signal.symbol, subscription):
                        logger.debug(f"Symbol {signal.symbol} filtered out for subscription {subscription.id}")
                        continue

                    # Map symbol if needed
                    symbol = signal.symbol
                    if subscription.symbol_mapping and signal.symbol in subscription.symbol_mapping:
                        symbol = subscription.symbol_mapping[signal.symbol]

                    # Calculate lot sizes for each TP
                    take_profits = signal.take_profits or []
                    if not take_profits:
                        take_profits = [None]  # Single trade with no TP

                    lot_size = subscription.lot_size or 0.01  # Default to 0.01
                    ratios = subscription.get_tp_ratios(len(take_profits))

                    for i, (tp, ratio) in enumerate(zip(take_profits, ratios)):
                        volume = round(lot_size * ratio / 100, 2)
                        volume = max(0.01, min(volume, subscription.max_lot_size))

                        trade = Trade(
                            tenant_id=signal.tenant_id,
                            parsed_signal_id=signal.id,
                            mt5_account_id=subscription.mt5_account_id,
                            symbol=symbol,
                            direction=signal.direction,
                            volume=volume,
                            entry_price=signal.entry_price,
                            stop_loss=signal.stop_loss,
                            take_profit=tp,
                            tp_level=i + 1 if tp else None,
                            status=TradeStatus.PENDING,
                        )

                        db.add(trade)
                        trades_created += 1

                except Exception as e:
                    logger.error(f"Error creating trade for subscription {subscription.id}: {e}")
                    trades_failed += 1

            await db.commit()

            # Update signal status
            if trades_created > 0:
                signal.status = SignalStatus.EXECUTED if trades_failed == 0 else SignalStatus.PARTIAL
            else:
                signal.status = SignalStatus.FAILED
                signal.error_message = "No trades created"

            await db.commit()

            # Queue trade execution
            from workers.tasks.trade_tasks import execute_trade

            result = await db.execute(
                select(Trade).where(
                    Trade.parsed_signal_id == signal.id,
                    Trade.status == TradeStatus.PENDING,
                )
            )
            pending_trades = result.scalars().all()

            for trade in pending_trades:
                execute_trade.delay(str(trade.id))

            logger.info(f"Signal {signal_id} processed: {trades_created} trades created, {trades_failed} failed")

            return {
                "success": True,
                "trades_created": trades_created,
                "trades_failed": trades_failed,
            }

        except Exception as e:
            logger.error(f"Error processing signal {signal_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


def _check_symbol_filter(symbol: str, subscription: SignalSubscription) -> bool:
    """Check if symbol passes subscription filters."""
    # Check whitelist
    if subscription.allowed_symbols:
        if symbol not in subscription.allowed_symbols:
            return False

    # Check blacklist
    if subscription.blocked_symbols:
        if symbol in subscription.blocked_symbols:
            return False

    return True


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_telegram_message(
    self,
    message_data: dict,
) -> dict:
    """Process a Telegram message and create signal.

    Args:
        message_data: Message data from Telegram listener

    Returns:
        dict with processing result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _process_telegram_message_async(self, message_data)
    )


async def _process_telegram_message_async(task, message_data: dict) -> dict:
    """Async implementation of Telegram message processing."""
    async with async_session_maker() as db:
        try:
            tenant_id = message_data.get("tenant_id")
            channel_db_id = message_data.get("channel_db_id")
            text = message_data.get("text", "")
            message_id = message_data.get("message_id")

            if not tenant_id or not text:
                return {"success": False, "error": "Missing tenant_id or text"}

            # Create raw signal
            raw_signal = RawSignal(
                tenant_id=UUID(tenant_id),
                channel_id=UUID(channel_db_id) if channel_db_id else None,
                source_type=SourceType.TELEGRAM,
                source_message_id=message_id,
                raw_text=text,
            )

            db.add(raw_signal)
            await db.flush()

            # Parse signal
            parser = SignalParser()
            parsed = parser.parse(text)

            if not parsed:
                raw_signal.is_processed = True
                await db.commit()
                logger.debug(f"Message not recognized as signal: {text[:100]}")
                return {"success": True, "is_signal": False}

            # Create parsed signal
            parsed_signal = ParsedSignal(
                tenant_id=UUID(tenant_id),
                raw_signal_id=raw_signal.id,
                symbol=parsed["symbol"],
                direction=parsed["direction"],
                entry_price=parsed.get("entry_price"),
                entry_price_low=parsed.get("entry_price_low"),
                entry_price_high=parsed.get("entry_price_high"),
                stop_loss=parsed["stop_loss"],
                take_profits=parsed.get("take_profits", []),
                parser_confidence=parsed.get("confidence"),
                parser_notes=parsed.get("notes"),
                status=SignalStatus.PENDING,
            )

            db.add(parsed_signal)
            raw_signal.is_processed = True
            await db.commit()

            logger.info(f"Parsed signal from Telegram: {parsed['direction']} {parsed['symbol']}")

            # Queue signal processing
            process_signal.delay(str(parsed_signal.id))

            return {
                "success": True,
                "is_signal": True,
                "signal_id": str(parsed_signal.id),
            }

        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


@app.task
def cleanup_expired_signals() -> dict:
    """Clean up expired signals.

    Returns:
        dict with cleanup result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_cleanup_expired_signals_async())


async def _cleanup_expired_signals_async() -> dict:
    """Async implementation of expired signal cleanup."""
    async with async_session_maker() as db:
        try:
            now = datetime.utcnow()

            # Find expired signals
            result = await db.execute(
                select(ParsedSignal).where(
                    ParsedSignal.status == SignalStatus.PENDING,
                    ParsedSignal.expires_at < now,
                )
            )
            expired_signals = result.scalars().all()

            count = 0
            for signal in expired_signals:
                signal.status = SignalStatus.EXPIRED
                count += 1

            await db.commit()

            logger.info(f"Marked {count} signals as expired")

            return {
                "success": True,
                "expired_count": count,
            }

        except Exception as e:
            logger.error(f"Error cleaning up expired signals: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
