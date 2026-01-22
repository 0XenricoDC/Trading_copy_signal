"""Signals API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.deps import CurrentTenant, TenantDB
from backend.app.models.signal import RawSignal, ParsedSignal, SourceType, SignalStatus
from backend.app.schemas.signal import (
    RawSignalResponse,
    ParsedSignalResponse,
    SignalParsePreview,
    ManualSignalRequest,
    ParsedSignalCreate,
)

router = APIRouter()


@router.get("", response_model=list[ParsedSignalResponse])
async def list_signals(
    tenant: CurrentTenant,
    db: TenantDB,
    skip: int = 0,
    limit: int = 100,
    status_filter: SignalStatus | None = None,
):
    """List all parsed signals for the current tenant."""
    query = (
        select(ParsedSignal)
        .where(ParsedSignal.tenant_id == tenant.id)
        .offset(skip)
        .limit(limit)
        .order_by(ParsedSignal.created_at.desc())
    )

    if status_filter:
        query = query.where(ParsedSignal.status == status_filter)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/raw", response_model=list[RawSignalResponse])
async def list_raw_signals(
    tenant: CurrentTenant,
    db: TenantDB,
    skip: int = 0,
    limit: int = 100,
    processed_only: bool | None = None,
):
    """List all raw signals for the current tenant."""
    query = (
        select(RawSignal)
        .where(RawSignal.tenant_id == tenant.id)
        .offset(skip)
        .limit(limit)
        .order_by(RawSignal.received_at.desc())
    )

    if processed_only is not None:
        query = query.where(RawSignal.is_processed == processed_only)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{signal_id}", response_model=ParsedSignalResponse)
async def get_signal(
    signal_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Get a specific parsed signal."""
    result = await db.execute(
        select(ParsedSignal).where(
            ParsedSignal.id == signal_id,
            ParsedSignal.tenant_id == tenant.id,
        )
    )
    signal = result.scalar_one_or_none()

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found",
        )

    return signal


@router.post("/parse-preview", response_model=SignalParsePreview)
async def parse_preview(
    request: ManualSignalRequest,
    tenant: CurrentTenant,
):
    """Preview signal parsing without saving to database."""
    from workers.parsers.regex_parser import SignalParser

    if request.raw_text:
        parser = SignalParser()
        result = parser.parse(request.raw_text)

        if result:
            return SignalParsePreview(
                success=True,
                parsed_signal=ParsedSignalCreate(
                    symbol=result["symbol"],
                    direction=result["direction"],
                    entry_price=result.get("entry_price"),
                    entry_price_low=result.get("entry_price_low"),
                    entry_price_high=result.get("entry_price_high"),
                    stop_loss=result["stop_loss"],
                    take_profits=result.get("take_profits", []),
                ),
                confidence=result.get("confidence", 0.0),
                notes=result.get("notes"),
                raw_text=request.raw_text,
            )
        else:
            return SignalParsePreview(
                success=False,
                errors=["Could not parse signal from text"],
                raw_text=request.raw_text,
            )
    elif all([request.symbol, request.direction, request.stop_loss]):
        # Direct values provided
        return SignalParsePreview(
            success=True,
            parsed_signal=ParsedSignalCreate(
                symbol=request.symbol,
                direction=request.direction,
                entry_price=request.entry_price,
                stop_loss=request.stop_loss,
                take_profits=request.take_profits or [],
            ),
            confidence=1.0,
            notes="Direct values provided",
            raw_text=request.raw_text or "",
        )
    else:
        return SignalParsePreview(
            success=False,
            errors=["Either raw_text or symbol/direction/stop_loss must be provided"],
            raw_text=request.raw_text or "",
        )


@router.post("/manual", response_model=ParsedSignalResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_signal(
    request: ManualSignalRequest,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Create a manual signal and trigger trade execution."""
    from workers.parsers.regex_parser import SignalParser

    parsed_data = None

    if request.raw_text:
        # Parse the raw text
        parser = SignalParser()
        parsed_data = parser.parse(request.raw_text)

        if not parsed_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not parse signal from text",
            )

        # Save raw signal
        raw_signal = RawSignal(
            tenant_id=tenant.id,
            source_type=SourceType.MANUAL,
            raw_text=request.raw_text,
        )
        db.add(raw_signal)
        await db.flush()

        # Create parsed signal
        parsed_signal = ParsedSignal(
            tenant_id=tenant.id,
            raw_signal_id=raw_signal.id,
            symbol=parsed_data["symbol"],
            direction=parsed_data["direction"],
            entry_price=parsed_data.get("entry_price"),
            entry_price_low=parsed_data.get("entry_price_low"),
            entry_price_high=parsed_data.get("entry_price_high"),
            stop_loss=parsed_data["stop_loss"],
            take_profits=parsed_data.get("take_profits", []),
            parser_confidence=parsed_data.get("confidence"),
            parser_notes=parsed_data.get("notes"),
        )

    elif all([request.symbol, request.direction, request.stop_loss]):
        # Direct values provided
        parsed_signal = ParsedSignal(
            tenant_id=tenant.id,
            symbol=request.symbol,
            direction=request.direction,
            entry_price=request.entry_price,
            stop_loss=request.stop_loss,
            take_profits=request.take_profits or [],
            parser_confidence=1.0,
            parser_notes="Manual entry",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either raw_text or symbol/direction/stop_loss must be provided",
        )

    db.add(parsed_signal)
    await db.flush()
    await db.refresh(parsed_signal)

    # Queue trade execution via Celery
    # TODO: Implement Celery task for trade execution
    # from workers.tasks.signal_tasks import process_signal
    # process_signal.delay(str(parsed_signal.id), request.subscription_ids)

    return parsed_signal


@router.post("/{signal_id}/execute", response_model=ParsedSignalResponse)
async def execute_signal(
    signal_id: UUID,
    subscription_ids: list[UUID] | None = None,
    tenant: CurrentTenant = None,
    db: TenantDB = None,
):
    """Execute a pending signal on specified subscriptions."""
    result = await db.execute(
        select(ParsedSignal).where(
            ParsedSignal.id == signal_id,
            ParsedSignal.tenant_id == tenant.id,
        )
    )
    signal = result.scalar_one_or_none()

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found",
        )

    if signal.status not in [SignalStatus.PENDING, SignalStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signal cannot be executed in status: {signal.status}",
        )

    # Update status to processing
    signal.status = SignalStatus.PROCESSING
    await db.flush()

    # TODO: Queue trade execution via Celery
    # from workers.tasks.signal_tasks import process_signal
    # process_signal.delay(str(signal.id), subscription_ids)

    await db.refresh(signal)
    return signal


@router.post("/{signal_id}/cancel", response_model=ParsedSignalResponse)
async def cancel_signal(
    signal_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Cancel a pending signal."""
    result = await db.execute(
        select(ParsedSignal).where(
            ParsedSignal.id == signal_id,
            ParsedSignal.tenant_id == tenant.id,
        )
    )
    signal = result.scalar_one_or_none()

    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found",
        )

    if signal.status not in [SignalStatus.PENDING, SignalStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signal cannot be cancelled in status: {signal.status}",
        )

    signal.status = SignalStatus.CANCELLED
    await db.flush()
    await db.refresh(signal)

    return signal
