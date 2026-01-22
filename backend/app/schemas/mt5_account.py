"""MT5 Account schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MT5AccountBase(BaseModel):
    """Base MT5 account schema."""

    name: str
    login: int
    server: str
    mt5_path: str | None = None
    is_demo: bool = True


class MT5AccountCreate(MT5AccountBase):
    """Schema for creating an MT5 account."""

    password: str  # Plain password, will be encrypted


class MT5AccountUpdate(BaseModel):
    """Schema for updating an MT5 account."""

    name: str | None = None
    password: str | None = None  # If provided, will re-encrypt
    server: str | None = None
    mt5_path: str | None = None
    is_active: bool | None = None
    is_demo: bool | None = None


class MT5AccountResponse(MT5AccountBase):
    """Schema for MT5 account response (no password)."""

    id: UUID
    tenant_id: UUID
    is_active: bool
    last_connected: datetime | None = None
    last_balance: float | None = None
    last_equity: float | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MT5AccountTestResult(BaseModel):
    """Schema for MT5 connection test result."""

    success: bool
    message: str
    balance: float | None = None
    equity: float | None = None
    margin_free: float | None = None
    leverage: int | None = None
    server_time: datetime | None = None


class MT5Position(BaseModel):
    """Schema for an MT5 position."""

    ticket: int
    symbol: str
    type: str  # "buy" or "sell"
    volume: float
    open_price: float
    current_price: float
    stop_loss: float | None = None
    take_profit: float | None = None
    profit: float
    swap: float
    commission: float
    open_time: datetime
    magic: int | None = None
    comment: str | None = None
