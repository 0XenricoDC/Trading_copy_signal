"""Telegram channel schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TelegramChannelBase(BaseModel):
    """Base telegram channel schema."""

    channel_id: int
    channel_name: str
    channel_username: str | None = None
    description: str | None = None


class TelegramChannelCreate(TelegramChannelBase):
    """Schema for creating a telegram channel."""

    pass


class TelegramChannelUpdate(BaseModel):
    """Schema for updating a telegram channel."""

    channel_name: str | None = None
    channel_username: str | None = None
    description: str | None = None
    is_active: bool | None = None


class TelegramChannelResponse(TelegramChannelBase):
    """Schema for telegram channel response."""

    id: UUID
    tenant_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
