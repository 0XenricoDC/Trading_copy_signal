"""Signal subscription schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from backend.app.models.subscription import TPStrategy


class SubscriptionBase(BaseModel):
    """Base subscription schema."""

    channel_id: UUID
    mt5_account_id: UUID
    name: str | None = None
    lot_size: float | None = None
    risk_percent: float | None = None
    max_lot_size: float = 10.0
    tp_strategy: TPStrategy = TPStrategy.EQUAL
    tp_split_ratios: list[float] | None = None
    symbol_mapping: dict[str, str] | None = None
    allowed_symbols: list[str] | None = None
    blocked_symbols: list[str] | None = None
    min_sl_pips: float | None = None
    max_sl_pips: float | None = None

    @field_validator("tp_split_ratios")
    @classmethod
    def validate_ratios(cls, v: list[float] | None) -> list[float] | None:
        if v is not None:
            total = sum(v)
            if not (99.0 <= total <= 101.0):  # Allow small rounding errors
                raise ValueError("TP split ratios must sum to 100")
        return v

    @field_validator("risk_percent")
    @classmethod
    def validate_risk(cls, v: float | None) -> float | None:
        if v is not None and (v <= 0 or v > 100):
            raise ValueError("Risk percent must be between 0 and 100")
        return v


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription."""

    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription."""

    name: str | None = None
    lot_size: float | None = None
    risk_percent: float | None = None
    max_lot_size: float | None = None
    tp_strategy: TPStrategy | None = None
    tp_split_ratios: list[float] | None = None
    symbol_mapping: dict[str, str] | None = None
    allowed_symbols: list[str] | None = None
    blocked_symbols: list[str] | None = None
    min_sl_pips: float | None = None
    max_sl_pips: float | None = None
    is_active: bool | None = None


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response."""

    id: UUID
    tenant_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Nested info
    channel_name: str | None = None
    mt5_account_name: str | None = None

    class Config:
        from_attributes = True
