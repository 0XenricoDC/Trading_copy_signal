"""Trade execution tasks."""

import logging
from datetime import datetime
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from workers.celery_app import app
from workers.mt5.pool_manager import get_pool_manager
from backend.app.core.security import decrypt_credentials
from backend.app.db.session import async_session_maker
from backend.app.models.mt5_account import MT5Account
from backend.app.models.trade import Trade, TradeStatus
from backend.app.models.signal import ParsedSignal, SignalStatus

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=5)
def execute_trade(
    self,
    trade_id: str,
) -> dict:
    """Execute a trade on MT5.

    Args:
        trade_id: UUID of the trade to execute

    Returns:
        dict with execution result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_execute_trade_async(self, trade_id))


async def _execute_trade_async(task, trade_id: str) -> dict:
    """Async implementation of trade execution."""
    async with async_session_maker() as db:
        try:
            # Get trade
            result = await db.execute(
                select(Trade).where(Trade.id == UUID(trade_id))
            )
            trade = result.scalar_one_or_none()

            if not trade:
                return {"success": False, "error": "Trade not found"}

            if trade.status != TradeStatus.PENDING:
                return {"success": False, "error": f"Trade in invalid status: {trade.status}"}

            # Get MT5 account
            result = await db.execute(
                select(MT5Account).where(MT5Account.id == trade.mt5_account_id)
            )
            account = result.scalar_one_or_none()

            if not account:
                trade.status = TradeStatus.FAILED
                trade.error_message = "MT5 account not found"
                await db.commit()
                return {"success": False, "error": "MT5 account not found"}

            # Decrypt password
            password = decrypt_credentials(account.encrypted_password)

            # Get connection
            pool = get_pool_manager()
            connection = pool.get_connection(
                account_id=str(account.id),
                login=account.login,
                password=password,
                server=account.server,
                mt5_path=account.mt5_path,
            )

            if connection is None:
                trade.status = TradeStatus.FAILED
                trade.error_message = "Failed to connect to MT5"
                trade.retry_count += 1
                await db.commit()

                # Retry
                if trade.retry_count < 3:
                    task.retry()

                return {"success": False, "error": "Failed to connect to MT5"}

            connector, executor = connection

            try:
                # Update trade status
                trade.status = TradeStatus.OPENING
                await db.commit()

                # Execute trade
                direction = "buy" if trade.direction.value == "buy" else "sell"
                result = executor.open_position(
                    symbol=trade.symbol,
                    direction=direction,
                    volume=trade.volume,
                    stop_loss=trade.stop_loss,
                    take_profit=trade.take_profit,
                    price=trade.entry_price,
                    comment=f"TC-{str(trade.id)[:8]}",
                )

                if result.success:
                    trade.status = TradeStatus.OPEN
                    trade.mt5_ticket = result.ticket
                    trade.mt5_order_id = result.order_id
                    trade.open_price = result.price
                    trade.opened_at = datetime.utcnow()
                    await db.commit()

                    logger.info(f"Trade {trade_id} executed: ticket {result.ticket}")

                    return {
                        "success": True,
                        "ticket": result.ticket,
                        "price": result.price,
                        "volume": result.volume,
                    }
                else:
                    trade.status = TradeStatus.FAILED
                    trade.error_code = result.error_code
                    trade.error_message = result.error_message
                    trade.retry_count += 1
                    await db.commit()

                    logger.error(f"Trade {trade_id} failed: {result.error_message}")

                    # Retry if retryable error
                    if trade.retry_count < 3:
                        task.retry()

                    return {
                        "success": False,
                        "error": result.error_message,
                        "error_code": result.error_code,
                    }

            finally:
                pool.release_connection(str(account.id))

        except Exception as e:
            logger.error(f"Error executing trade {trade_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


@app.task(bind=True, max_retries=3, default_retry_delay=5)
def close_trade(
    self,
    trade_id: str,
    volume: float | None = None,
) -> dict:
    """Close a trade on MT5.

    Args:
        trade_id: UUID of the trade to close
        volume: Volume to close (None for full position)

    Returns:
        dict with close result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_close_trade_async(self, trade_id, volume))


async def _close_trade_async(task, trade_id: str, volume: float | None) -> dict:
    """Async implementation of trade close."""
    async with async_session_maker() as db:
        try:
            # Get trade
            result = await db.execute(
                select(Trade).where(Trade.id == UUID(trade_id))
            )
            trade = result.scalar_one_or_none()

            if not trade:
                return {"success": False, "error": "Trade not found"}

            if trade.status != TradeStatus.OPEN and trade.status != TradeStatus.CLOSING:
                return {"success": False, "error": f"Trade in invalid status: {trade.status}"}

            if not trade.mt5_ticket:
                return {"success": False, "error": "Trade has no MT5 ticket"}

            # Get MT5 account
            result = await db.execute(
                select(MT5Account).where(MT5Account.id == trade.mt5_account_id)
            )
            account = result.scalar_one_or_none()

            if not account:
                return {"success": False, "error": "MT5 account not found"}

            # Decrypt password
            password = decrypt_credentials(account.encrypted_password)

            # Get connection
            pool = get_pool_manager()
            connection = pool.get_connection(
                account_id=str(account.id),
                login=account.login,
                password=password,
                server=account.server,
                mt5_path=account.mt5_path,
            )

            if connection is None:
                trade.retry_count += 1
                await db.commit()

                if trade.retry_count < 3:
                    task.retry()

                return {"success": False, "error": "Failed to connect to MT5"}

            connector, executor = connection

            try:
                # Update trade status
                trade.status = TradeStatus.CLOSING
                await db.commit()

                # Close trade
                result = executor.close_position(
                    ticket=trade.mt5_ticket,
                    volume=volume,
                    comment=f"TC-Close-{str(trade.id)[:8]}",
                )

                if result.success:
                    trade.status = TradeStatus.CLOSED
                    trade.close_price = result.price
                    trade.closed_at = datetime.utcnow()

                    # Calculate profit (would need to get from MT5)
                    # trade.profit = ...

                    await db.commit()

                    logger.info(f"Trade {trade_id} closed at {result.price}")

                    return {
                        "success": True,
                        "price": result.price,
                    }
                else:
                    trade.status = TradeStatus.OPEN  # Revert status
                    trade.error_message = result.error_message
                    trade.retry_count += 1
                    await db.commit()

                    logger.error(f"Failed to close trade {trade_id}: {result.error_message}")

                    if trade.retry_count < 3:
                        task.retry()

                    return {
                        "success": False,
                        "error": result.error_message,
                    }

            finally:
                pool.release_connection(str(account.id))

        except Exception as e:
            logger.error(f"Error closing trade {trade_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


@app.task
def test_mt5_connection(account_id: str) -> dict:
    """Test MT5 account connection.

    Args:
        account_id: UUID of the MT5 account to test

    Returns:
        dict with connection test result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_test_connection_async(account_id))


async def _test_connection_async(account_id: str) -> dict:
    """Async implementation of connection test."""
    async with async_session_maker() as db:
        try:
            # Get account
            result = await db.execute(
                select(MT5Account).where(MT5Account.id == UUID(account_id))
            )
            account = result.scalar_one_or_none()

            if not account:
                return {
                    "success": False,
                    "message": "Account not found",
                }

            # Decrypt password
            password = decrypt_credentials(account.encrypted_password)

            # Get connection
            pool = get_pool_manager()
            connection = pool.get_connection(
                account_id=str(account.id),
                login=account.login,
                password=password,
                server=account.server,
                mt5_path=account.mt5_path,
            )

            if connection is None:
                return {
                    "success": False,
                    "message": "Failed to connect to MT5",
                }

            connector, executor = connection

            try:
                # Get account info
                info = connector.get_account_info()

                if info:
                    # Update account with latest info
                    account.last_connected = datetime.utcnow()
                    account.last_balance = info.get("balance")
                    account.last_equity = info.get("equity")
                    await db.commit()

                    return {
                        "success": True,
                        "message": "Connection successful",
                        "balance": info.get("balance"),
                        "equity": info.get("equity"),
                        "margin_free": info.get("margin_free"),
                        "leverage": info.get("leverage"),
                        "server_time": datetime.utcnow().isoformat(),
                    }
                else:
                    return {
                        "success": False,
                        "message": "Connected but failed to get account info",
                    }

            finally:
                pool.release_connection(str(account.id))

        except Exception as e:
            logger.error(f"Error testing connection for {account_id}: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e),
            }
