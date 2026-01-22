"""Trades API endpoints."""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.app.core.deps import CurrentTenant, TenantDB
from backend.app.models.trade import Trade, TradeStatus
from backend.app.models.signal import SignalDirection
from backend.app.schemas.trade import TradeResponse, TradeStats

router = APIRouter()


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    tenant: CurrentTenant,
    db: TenantDB,
    skip: int = 0,
    limit: int = 100,
    status_filter: TradeStatus | None = None,
    mt5_account_id: UUID | None = None,
    symbol: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
):
    """List all trades for the current tenant."""
    query = (
        select(Trade)
        .where(Trade.tenant_id == tenant.id)
        .options(selectinload(Trade.mt5_account))
        .offset(skip)
        .limit(limit)
        .order_by(Trade.created_at.desc())
    )

    if status_filter:
        query = query.where(Trade.status == status_filter)

    if mt5_account_id:
        query = query.where(Trade.mt5_account_id == mt5_account_id)

    if symbol:
        query = query.where(Trade.symbol == symbol)

    if from_date:
        query = query.where(Trade.created_at >= from_date)

    if to_date:
        query = query.where(Trade.created_at <= to_date)

    result = await db.execute(query)
    trades = result.scalars().all()

    # Add account names
    response = []
    for trade in trades:
        trade_dict = TradeResponse.model_validate(trade).model_dump()
        trade_dict["mt5_account_name"] = trade.mt5_account.name if trade.mt5_account else None
        response.append(TradeResponse(**trade_dict))

    return response


@router.get("/stats", response_model=TradeStats)
async def get_trade_stats(
    tenant: CurrentTenant,
    db: TenantDB,
    mt5_account_id: UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
):
    """Get trade statistics for the current tenant."""
    # Base filter
    filters = [Trade.tenant_id == tenant.id]

    if mt5_account_id:
        filters.append(Trade.mt5_account_id == mt5_account_id)

    if from_date:
        filters.append(Trade.created_at >= from_date)

    if to_date:
        filters.append(Trade.created_at <= to_date)

    base_filter = and_(*filters)

    # Total trades
    result = await db.execute(
        select(func.count(Trade.id)).where(base_filter)
    )
    total_trades = result.scalar() or 0

    # Open trades
    result = await db.execute(
        select(func.count(Trade.id)).where(
            base_filter,
            Trade.status == TradeStatus.OPEN,
        )
    )
    open_trades = result.scalar() or 0

    # Closed trades
    result = await db.execute(
        select(func.count(Trade.id)).where(
            base_filter,
            Trade.status == TradeStatus.CLOSED,
        )
    )
    closed_trades = result.scalar() or 0

    # Winning trades (profit > 0)
    result = await db.execute(
        select(func.count(Trade.id)).where(
            base_filter,
            Trade.status == TradeStatus.CLOSED,
            Trade.profit > 0,
        )
    )
    winning_trades = result.scalar() or 0

    # Losing trades (profit < 0)
    result = await db.execute(
        select(func.count(Trade.id)).where(
            base_filter,
            Trade.status == TradeStatus.CLOSED,
            Trade.profit < 0,
        )
    )
    losing_trades = result.scalar() or 0

    # Total profit
    result = await db.execute(
        select(func.coalesce(func.sum(Trade.profit), 0)).where(
            base_filter,
            Trade.status == TradeStatus.CLOSED,
        )
    )
    total_profit = result.scalar() or 0.0

    # Total commission
    result = await db.execute(
        select(func.coalesce(func.sum(Trade.commission), 0)).where(
            base_filter,
        )
    )
    total_commission = result.scalar() or 0.0

    # Total swap
    result = await db.execute(
        select(func.coalesce(func.sum(Trade.swap), 0)).where(
            base_filter,
        )
    )
    total_swap = result.scalar() or 0.0

    # Best and worst trade
    result = await db.execute(
        select(func.max(Trade.profit)).where(
            base_filter,
            Trade.status == TradeStatus.CLOSED,
        )
    )
    best_trade = result.scalar()

    result = await db.execute(
        select(func.min(Trade.profit)).where(
            base_filter,
            Trade.status == TradeStatus.CLOSED,
        )
    )
    worst_trade = result.scalar()

    # Calculate derived stats
    win_rate = None
    average_profit = None
    average_loss = None
    profit_factor = None

    if closed_trades > 0:
        win_rate = (winning_trades / closed_trades) * 100

    if winning_trades > 0:
        result = await db.execute(
            select(func.avg(Trade.profit)).where(
                base_filter,
                Trade.status == TradeStatus.CLOSED,
                Trade.profit > 0,
            )
        )
        average_profit = result.scalar()

    if losing_trades > 0:
        result = await db.execute(
            select(func.avg(Trade.profit)).where(
                base_filter,
                Trade.status == TradeStatus.CLOSED,
                Trade.profit < 0,
            )
        )
        average_loss = result.scalar()

    # Profit factor = gross profit / abs(gross loss)
    if average_loss and average_loss < 0:
        result = await db.execute(
            select(func.sum(Trade.profit)).where(
                base_filter,
                Trade.status == TradeStatus.CLOSED,
                Trade.profit > 0,
            )
        )
        gross_profit = result.scalar() or 0

        result = await db.execute(
            select(func.sum(Trade.profit)).where(
                base_filter,
                Trade.status == TradeStatus.CLOSED,
                Trade.profit < 0,
            )
        )
        gross_loss = result.scalar() or 0

        if gross_loss < 0:
            profit_factor = gross_profit / abs(gross_loss)

    return TradeStats(
        total_trades=total_trades,
        open_trades=open_trades,
        closed_trades=closed_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        total_profit=total_profit,
        total_commission=total_commission,
        total_swap=total_swap,
        win_rate=win_rate,
        average_profit=average_profit,
        average_loss=average_loss,
        profit_factor=profit_factor,
        best_trade=best_trade,
        worst_trade=worst_trade,
        period_start=from_date,
        period_end=to_date,
    )


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Get a specific trade."""
    result = await db.execute(
        select(Trade)
        .where(
            Trade.id == trade_id,
            Trade.tenant_id == tenant.id,
        )
        .options(selectinload(Trade.mt5_account))
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )

    response = TradeResponse.model_validate(trade)
    response.mt5_account_name = trade.mt5_account.name if trade.mt5_account else None

    return response


@router.post("/{trade_id}/close")
async def close_trade(
    trade_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Close an open trade."""
    result = await db.execute(
        select(Trade).where(
            Trade.id == trade_id,
            Trade.tenant_id == tenant.id,
        )
    )
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found",
        )

    if trade.status != TradeStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trade cannot be closed in status: {trade.status}",
        )

    # TODO: Queue close trade via Celery
    # from workers.tasks.trade_tasks import close_trade_task
    # close_trade_task.delay(str(trade.id))

    trade.status = TradeStatus.CLOSING
    await db.flush()
    await db.refresh(trade)

    return {"message": "Trade close request queued", "trade_id": str(trade.id)}
