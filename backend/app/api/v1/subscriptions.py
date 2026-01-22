"""Signal Subscriptions API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.deps import CurrentTenant, TenantDB
from backend.app.models.subscription import SignalSubscription
from backend.app.models.telegram_channel import TelegramChannel
from backend.app.models.mt5_account import MT5Account
from backend.app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
)

router = APIRouter()


@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    tenant: CurrentTenant,
    db: TenantDB,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
):
    """List all subscriptions for the current tenant."""
    query = (
        select(SignalSubscription)
        .where(SignalSubscription.tenant_id == tenant.id)
        .options(
            selectinload(SignalSubscription.channel),
            selectinload(SignalSubscription.mt5_account),
        )
        .offset(skip)
        .limit(limit)
        .order_by(SignalSubscription.created_at.desc())
    )

    if active_only:
        query = query.where(SignalSubscription.is_active == True)

    result = await db.execute(query)
    subscriptions = result.scalars().all()

    # Add channel and account names to response
    response = []
    for sub in subscriptions:
        sub_dict = SubscriptionResponse.model_validate(sub).model_dump()
        sub_dict["channel_name"] = sub.channel.channel_name if sub.channel else None
        sub_dict["mt5_account_name"] = sub.mt5_account.name if sub.mt5_account else None
        response.append(SubscriptionResponse(**sub_dict))

    return response


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription: SubscriptionCreate,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Create a new subscription."""
    # Verify channel exists and belongs to tenant
    result = await db.execute(
        select(TelegramChannel).where(
            TelegramChannel.id == subscription.channel_id,
            TelegramChannel.tenant_id == tenant.id,
        )
    )
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found",
        )

    # Verify MT5 account exists and belongs to tenant
    result = await db.execute(
        select(MT5Account).where(
            MT5Account.id == subscription.mt5_account_id,
            MT5Account.tenant_id == tenant.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MT5 account not found",
        )

    # Check for duplicate subscription
    result = await db.execute(
        select(SignalSubscription).where(
            SignalSubscription.tenant_id == tenant.id,
            SignalSubscription.channel_id == subscription.channel_id,
            SignalSubscription.mt5_account_id == subscription.mt5_account_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription for this channel and account already exists",
        )

    db_subscription = SignalSubscription(
        tenant_id=tenant.id,
        **subscription.model_dump(),
    )

    db.add(db_subscription)
    await db.flush()
    await db.refresh(db_subscription)

    # Add channel and account names
    response = SubscriptionResponse.model_validate(db_subscription)
    response.channel_name = channel.channel_name
    response.mt5_account_name = account.name

    return response


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Get a specific subscription."""
    result = await db.execute(
        select(SignalSubscription)
        .where(
            SignalSubscription.id == subscription_id,
            SignalSubscription.tenant_id == tenant.id,
        )
        .options(
            selectinload(SignalSubscription.channel),
            selectinload(SignalSubscription.mt5_account),
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    response = SubscriptionResponse.model_validate(subscription)
    response.channel_name = subscription.channel.channel_name if subscription.channel else None
    response.mt5_account_name = subscription.mt5_account.name if subscription.mt5_account else None

    return response


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    subscription_update: SubscriptionUpdate,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Update a subscription."""
    result = await db.execute(
        select(SignalSubscription)
        .where(
            SignalSubscription.id == subscription_id,
            SignalSubscription.tenant_id == tenant.id,
        )
        .options(
            selectinload(SignalSubscription.channel),
            selectinload(SignalSubscription.mt5_account),
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    update_data = subscription_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subscription, field, value)

    await db.flush()
    await db.refresh(subscription)

    response = SubscriptionResponse.model_validate(subscription)
    response.channel_name = subscription.channel.channel_name if subscription.channel else None
    response.mt5_account_name = subscription.mt5_account.name if subscription.mt5_account else None

    return response


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Delete a subscription."""
    result = await db.execute(
        select(SignalSubscription).where(
            SignalSubscription.id == subscription_id,
            SignalSubscription.tenant_id == tenant.id,
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    await db.delete(subscription)
    await db.flush()
