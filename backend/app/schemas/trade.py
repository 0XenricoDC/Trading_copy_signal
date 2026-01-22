"""Trade schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.app.models.trade import TradeStatus
from backend.app.models.signal import SignalDirection


class TradeBase(BaseModel):
    """Base trade schema."""

    symbol: str
    direction: SignalDirection
    volume: float
    stop_loss: float
    take_profit: float | None = None


class TradeCreate(TradeBase):
    """Schema for creating a trade."""

    parsed_signal_id: UUID | None = None
    mt5_account_id: UUID
    entry_price: float | None = None
    tp_level: int | None = None


class TradeUpdate(BaseModel):
    """Schema for updating a trade."""

    status: TradeStatus | None = None
    mt5_ticket: int | None = None
    open_price: float | None = None
    close_price: float | None = None
    profit: float | None = None
    error_message: str | None = None


class TradeResponse(TradeBase):
    """Schema for trade response."""

    id: UUID
    tenant_id: UUID
    parsed_signal_id: UUID | None = None
    mt5_account_id: UUID
    mt5_ticket: int | None = None
    mt5_order_id: int | None = None
    entry_price: float | None = None
    tp_level: int | None = None
    status: TradeStatus
    open_price: float | None = None
    close_price: float | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    profit: float | None = None
    profit_pips: float | None = None
    commission: float | None = None
    swap: float | None = None
    error_code: int | None = None
    error_message: str | None = None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    # Computed/joined fields
    mt5_account_name: str | None = None

    class Config:
        from_attributes = True


class TradeStats(BaseModel):
    """Schema for trade statistics."""

    total_trades: int
    open_trades: int
    closed_trades: int
    winning_trades: int
    losing_trades: int
    total_profit: float
    total_commission: float
    total_swap: float
    win_rate: float | None = None
    average_profit: float | None = None
    average_loss: float | None = None
    profit_factor: float | None = None
    best_trade: float | None = None
    worst_trade: float | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
