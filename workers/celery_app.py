"""Celery application configuration."""

import os
import sys

from celery import Celery
from celery.schedules import crontab

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.config import settings

# Create Celery app
app = Celery(
    "tradecopy",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.tasks.trade_tasks",
        "workers.tasks.signal_tasks",
        "workers.tasks.sync_tasks",
    ],
)

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,

    # Result backend
    result_expires=3600,  # 1 hour

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for MT5
    worker_concurrency=4,

    # Task routes
    task_routes={
        "workers.tasks.trade_tasks.*": {"queue": "trades"},
        "workers.tasks.signal_tasks.*": {"queue": "signals"},
        "workers.tasks.sync_tasks.*": {"queue": "sync"},
    },

    # Default queue
    task_default_queue="default",

    # Beat schedule for periodic tasks
    beat_schedule={
        "sync-account-balances": {
            "task": "workers.tasks.sync_tasks.sync_all_account_balances",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        "cleanup-expired-signals": {
            "task": "workers.tasks.signal_tasks.cleanup_expired_signals",
            "schedule": crontab(minute="0", hour="*"),  # Every hour
        },
        "sync-open-positions": {
            "task": "workers.tasks.sync_tasks.sync_all_open_positions",
            "schedule": crontab(minute="*/1"),  # Every minute
        },
    },
)


if __name__ == "__main__":
    app.start()
