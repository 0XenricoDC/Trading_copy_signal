"""MT5 Accounts API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from backend.app.core.deps import CurrentTenant, TenantDB
from backend.app.core.security import encrypt_credentials, decrypt_credentials
from backend.app.models.mt5_account import MT5Account
from backend.app.schemas.mt5_account import (
    MT5AccountCreate,
    MT5AccountUpdate,
    MT5AccountResponse,
    MT5AccountTestResult,
    MT5Position,
)

router = APIRouter()


@router.get("", response_model=list[MT5AccountResponse])
async def list_accounts(
    tenant: CurrentTenant,
    db: TenantDB,
    skip: int = 0,
    limit: int = 100,
):
    """List all MT5 accounts for the current tenant."""
    result = await db.execute(
        select(MT5Account)
        .where(MT5Account.tenant_id == tenant.id)
        .offset(skip)
        .limit(limit)
        .order_by(MT5Account.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=MT5AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account: MT5AccountCreate,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Create a new MT5 account."""
    # Check if login already exists for this tenant
    result = await db.execute(
        select(MT5Account).where(
            MT5Account.tenant_id == tenant.id,
            MT5Account.login == account.login,
            MT5Account.server == account.server,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this login and server already exists",
        )

    # Encrypt the password
    encrypted_password = encrypt_credentials(account.password)

    db_account = MT5Account(
        tenant_id=tenant.id,
        name=account.name,
        login=account.login,
        encrypted_password=encrypted_password,
        server=account.server,
        mt5_path=account.mt5_path,
        is_demo=account.is_demo,
    )

    db.add(db_account)
    await db.flush()
    await db.refresh(db_account)

    return db_account


@router.get("/{account_id}", response_model=MT5AccountResponse)
async def get_account(
    account_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Get a specific MT5 account."""
    result = await db.execute(
        select(MT5Account).where(
            MT5Account.id == account_id,
            MT5Account.tenant_id == tenant.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return account


@router.put("/{account_id}", response_model=MT5AccountResponse)
async def update_account(
    account_id: UUID,
    account_update: MT5AccountUpdate,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Update an MT5 account."""
    result = await db.execute(
        select(MT5Account).where(
            MT5Account.id == account_id,
            MT5Account.tenant_id == tenant.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    update_data = account_update.model_dump(exclude_unset=True)

    # Handle password update separately
    if "password" in update_data:
        password = update_data.pop("password")
        if password:
            update_data["encrypted_password"] = encrypt_credentials(password)

    for field, value in update_data.items():
        setattr(account, field, value)

    await db.flush()
    await db.refresh(account)

    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Delete an MT5 account."""
    result = await db.execute(
        select(MT5Account).where(
            MT5Account.id == account_id,
            MT5Account.tenant_id == tenant.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    await db.delete(account)
    await db.flush()


@router.post("/{account_id}/test", response_model=MT5AccountTestResult)
async def test_connection(
    account_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Test MT5 account connection."""
    result = await db.execute(
        select(MT5Account).where(
            MT5Account.id == account_id,
            MT5Account.tenant_id == tenant.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # This will be implemented via Celery task to handle MT5 connection
    # For now, return a placeholder
    # TODO: Implement actual MT5 connection test via worker
    from workers.tasks.trade_tasks import test_mt5_connection

    try:
        result = await test_mt5_connection.apply_async(
            args=[str(account.id)],
        ).get(timeout=30)
        return MT5AccountTestResult(**result)
    except Exception as e:
        return MT5AccountTestResult(
            success=False,
            message=f"Connection test failed: {str(e)}",
        )


@router.get("/{account_id}/positions", response_model=list[MT5Position])
async def get_positions(
    account_id: UUID,
    tenant: CurrentTenant,
    db: TenantDB,
):
    """Get open positions for an MT5 account."""
    result = await db.execute(
        select(MT5Account).where(
            MT5Account.id == account_id,
            MT5Account.tenant_id == tenant.id,
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # TODO: Implement actual position fetching via worker
    # For now, return empty list
    return []
