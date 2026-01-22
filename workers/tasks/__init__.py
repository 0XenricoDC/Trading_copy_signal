"""Celery tasks."""

from workers.tasks.trade_tasks import (
    execute_trade,
    close_trade,
    test_mt5_connection,
)
from workers.tasks.signal_tasks import (
    process_signal,
    process_telegram_message,
    cleanup_expired_signals,
)
from workers.tasks.sync_tasks import (
    sync_account_balance,
    sync_all_account_balances,
    sync_open_positions,
    sync_all_open_positions,
)

__all__ = [
    "execute_trade",
    "close_trade",
    "test_mt5_connection",
    "process_signal",
    "process_telegram_message",
    "cleanup_expired_signals",
    "sync_account_balance",
    "sync_all_account_balances",
    "sync_open_positions",
    "sync_all_open_positions",
]
