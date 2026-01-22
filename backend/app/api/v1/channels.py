"""Telegram Channels API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete

from backend.app.core.deps import CurrentTenant, TenantDB
from backend.app.models.telegram_channel import TelegramChannel
from backend.app.schemas.telegram_channel import (
    TelegramChannelCreate,
    TelegramChannelUpdate,
    TelegramChannelResponse,
)

router = APIRouter()


@router.get("", response_model=list[TelegramChannelResponse])
async def list_channels(
    tenant: CurrentTenant,
    db: TenantDB,
    skip: int = 0,
    limit: int = 100,
):
    """List all Telegram channels for the current tenant."""
    result = await db.execute(
        select(TelegramChannel)
        .where(TelegramChannel.tenant_id == tenant.id)
        .offset(skip)
        .limit(limit)
        .order_by(TelegramChannel.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=TelegramChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel: TelegramChannelCreate,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Create a new Telegram channel."""
    # Check if channel already exists for this tenant
    result = await db.execute(
        select(TelegramChannel).where(
            TelegramChannel.tenant_id == tenant.id,
            TelegramChannel.channel_id == channel.channel_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Channel already registered",
        )

    db_channel = TelegramChannel(
        tenant_id=tenant.id,
        **channel.model_dump(),
    )

    db.add(db_channel)
    await db.flush()
    await db.refresh(db_channel)

    return db_channel


@router.get("/{channel_id}", response_model=TelegramChannelResponse)
async def get_channel(
    channel_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Get a specific Telegram channel."""
    result = await db.execute(
        select(TelegramChannel).where(
            TelegramChannel.id == channel_id,
            TelegramChannel.tenant_id == tenant.id,
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    return channel


@router.put("/{channel_id}", response_model=TelegramChannelResponse)
async def update_channel(
    channel_id: UUID,
    channel_update: TelegramChannelUpdate,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Update a Telegram channel."""
    result = await db.execute(
        select(TelegramChannel).where(
            TelegramChannel.id == channel_id,
            TelegramChannel.tenant_id == tenant.id,
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    update_data = channel_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)

    await db.flush()
    await db.refresh(channel)

    return channel


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Delete a Telegram channel."""
    result = await db.execute(
        select(TelegramChannel).where(
            TelegramChannel.id == channel_id,
            TelegramChannel.tenant_id == tenant.id,
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    await db.delete(channel)
    await db.flush()
