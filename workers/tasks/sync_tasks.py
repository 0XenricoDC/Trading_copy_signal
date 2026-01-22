"""Account synchronization tasks."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from workers.celery_app import app
from workers.mt5.pool_manager import get_pool_manager
from backend.app.core.security import decrypt_credentials
from backend.app.db.session import async_session_maker
from backend.app.models.mt5_account import MT5Account
from backend.app.models.trade import Trade, TradeStatus

logger = logging.getLogger(__name__)


@app.task
def sync_account_balance(account_id: str) -> dict:
    """Sync balance and equity for a single MT5 account.

    Args:
        account_id: UUID of the MT5 account

    Returns:
        dict with sync result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_sync_account_balance_async(account_id))


async def _sync_account_balance_async(account_id: str) -> dict:
    """Async implementation of account balance sync."""
    async with async_session_maker() as db:
        try:
            # Get account
            result = await db.execute(
                select(MT5Account).where(MT5Account.id == UUID(account_id))
            )
            account = result.scalar_one_or_none()

            if not account:
                return {"success": False, "error": "Account not found"}

            if not account.is_active:
                return {"success": False, "error": "Account is inactive"}

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
                return {"success": False, "error": "Failed to connect to MT5"}

            connector, executor = connection

            try:
                # Get account info
                info = connector.get_account_info()

                if info:
                    account.last_connected = datetime.utcnow()
                    account.last_balance = info.get("balance")
                    account.last_equity = info.get("equity")
                    await db.commit()

                    logger.debug(f"Synced account {account.login}: balance={info.get('balance')}")

                    return {
                        "success": True,
                        "balance": info.get("balance"),
                        "equity": info.get("equity"),
                    }
                else:
                    return {"success": False, "error": "Failed to get account info"}

            finally:
                pool.release_connection(str(account.id))

        except Exception as e:
            logger.error(f"Error syncing account {account_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


@app.task
def sync_all_account_balances() -> dict:
    """Sync balances for all active MT5 accounts.

    Returns:
        dict with sync result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_sync_all_account_balances_async())


async def _sync_all_account_balances_async() -> dict:
    """Async implementation of all account balance sync."""
    async with async_session_maker() as db:
        try:
            # Get all active accounts
            result = await db.execute(
                select(MT5Account).where(MT5Account.is_active == True)
            )
            accounts = result.scalars().all()

            success_count = 0
            fail_count = 0

            for account in accounts:
                try:
                    result = await _sync_account_balance_async(str(account.id))
                    if result.get("success"):
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    logger.error(f"Error syncing account {account.id}: {e}")
                    fail_count += 1

            logger.info(f"Account sync complete: {success_count} success, {fail_count} failed")

            return {
                "success": True,
                "synced": success_count,
                "failed": fail_count,
            }

        except Exception as e:
            logger.error(f"Error in sync_all_account_balances: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


@app.task
def sync_open_positions(account_id: str) -> dict:
    """Sync open positions for a single MT5 account.

    Updates trade records with current position data.

    Args:
        account_id: UUID of the MT5 account

    Returns:
        dict with sync result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_sync_open_positions_async(account_id))


async def _sync_open_positions_async(account_id: str) -> dict:
    """Async implementation of position sync."""
    async with async_session_maker() as db:
        try:
            # Get account
            result = await db.execute(
                select(MT5Account).where(MT5Account.id == UUID(account_id))
            )
            account = result.scalar_one_or_none()

            if not account:
                return {"success": False, "error": "Account not found"}

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
                return {"success": False, "error": "Failed to connect to MT5"}

            connector, executor = connection

            try:
                # Get open positions from MT5
                mt5_positions = connector.get_positions()
                mt5_tickets = {p["ticket"] for p in mt5_positions}

                # Get our open trades for this account
                result = await db.execute(
                    select(Trade).where(
                        Trade.mt5_account_id == account.id,
                        Trade.status == TradeStatus.OPEN,
                    )
                )
                our_trades = result.scalars().all()

                updated_count = 0
                closed_count = 0

                for trade in our_trades:
                    if trade.mt5_ticket:
                        if trade.mt5_ticket in mt5_tickets:
                            # Position still open - update profit
                            pos = next(
                                (p for p in mt5_positions if p["ticket"] == trade.mt5_ticket),
                                None
                            )
                            if pos:
                                trade.profit = pos["profit"]
                                trade.swap = pos["swap"]
                                trade.commission = pos.get("commission", 0)
                                updated_count += 1
                        else:
                            # Position closed (TP/SL hit or manual close)
                            trade.status = TradeStatus.CLOSED
                            trade.closed_at = datetime.utcnow()
                            closed_count += 1
                            logger.info(f"Trade {trade.id} (ticket {trade.mt5_ticket}) detected as closed")

                await db.commit()

                logger.debug(
                    f"Position sync for account {account.login}: "
                    f"{updated_count} updated, {closed_count} closed"
                )

                return {
                    "success": True,
                    "updated": updated_count,
                    "closed": closed_count,
                    "mt5_positions": len(mt5_positions),
                }

            finally:
                pool.release_connection(str(account.id))

        except Exception as e:
            logger.error(f"Error syncing positions for {account_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


@app.task
def sync_all_open_positions() -> dict:
    """Sync positions for all accounts with open trades.

    Returns:
        dict with sync result
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_sync_all_open_positions_async())


async def _sync_all_open_positions_async() -> dict:
    """Async implementation of all position sync."""
    async with async_session_maker() as db:
        try:
            # Get accounts with open trades
            result = await db.execute(
                select(Trade.mt5_account_id)
                .where(Trade.status == TradeStatus.OPEN)
                .distinct()
            )
            account_ids = [str(r[0]) for r in result.all()]

            success_count = 0
            fail_count = 0

            for account_id in account_ids:
                try:
                    result = await _sync_open_positions_async(account_id)
                    if result.get("success"):
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    logger.error(f"Error syncing positions for account {account_id}: {e}")
                    fail_count += 1

            logger.info(f"Position sync complete: {success_count} accounts synced, {fail_count} failed")

            return {
                "success": True,
                "synced": success_count,
                "failed": fail_count,
            }

        except Exception as e:
            logger.error(f"Error in sync_all_open_positions: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
