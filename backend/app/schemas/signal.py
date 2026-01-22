"""Signal schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.app.models.signal import SourceType, SignalDirection, SignalStatus


class RawSignalBase(BaseModel):
    """Base raw signal schema."""

    raw_text: str
    source_type: SourceType = SourceType.MANUAL


class RawSignalCreate(RawSignalBase):
    """Schema for creating a raw signal."""

    channel_id: UUID | None = None
    source_message_id: int | None = None


class RawSignalResponse(RawSignalBase):
    """Schema for raw signal response."""

    id: UUID
    tenant_id: UUID
    channel_id: UUID | None = None
    source_message_id: int | None = None
    received_at: datetime
    is_processed: bool

    class Config:
        from_attributes = True


class ParsedSignalBase(BaseModel):
    """Base parsed signal schema."""

    symbol: str
    direction: SignalDirection
    entry_price: float | None = None
    entry_price_low: float | None = None
    entry_price_high: float | None = None
    stop_loss: float
    take_profits: list[float] = []


class ParsedSignalCreate(ParsedSignalBase):
    """Schema for creating a parsed signal."""

    raw_signal_id: UUID | None = None


class ParsedSignalResponse(ParsedSignalBase):
    """Schema for parsed signal response."""

    id: UUID
    tenant_id: UUID
    raw_signal_id: UUID | None = None
    status: SignalStatus
    parser_confidence: float | None = None
    parser_notes: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None

    class Config:
        from_attributes = True


class SignalParsePreview(BaseModel):
    """Schema for signal parse preview (without saving)."""

    success: bool
    parsed_signal: ParsedSignalBase | None = None
    confidence: float | None = None
    notes: str | None = None
    errors: list[str] = []
    raw_text: str


class ManualSignalRequest(BaseModel):
    """Schema for manually entering a signal."""

    raw_text: str | None = None  # Will be parsed
    # Or direct values
    symbol: str | None = None
    direction: SignalDirection | None = None
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profits: list[float] | None = None
    # Target subscriptions (if not specified, all active subscriptions)
    subscription_ids: list[UUID] | None = None
