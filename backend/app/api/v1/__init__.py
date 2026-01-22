"""API v1 router aggregation."""

from fastapi import APIRouter

from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.channels import router as channels_router
from backend.app.api.v1.mt5_accounts import router as mt5_accounts_router
from backend.app.api.v1.subscriptions import router as subscriptions_router
from backend.app.api.v1.signals import router as signals_router
from backend.app.api.v1.trades import router as trades_router
from backend.app.api.v1.websocket import router as websocket_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(channels_router, prefix="/channels", tags=["Telegram Channels"])
router.include_router(mt5_accounts_router, prefix="/mt5-accounts", tags=["MT5 Accounts"])
router.include_router(subscriptions_router, prefix="/subscriptions", tags=["Subscriptions"])
router.include_router(signals_router, prefix="/signals", tags=["Signals"])
router.include_router(trades_router, prefix="/trades", tags=["Trades"])
router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
