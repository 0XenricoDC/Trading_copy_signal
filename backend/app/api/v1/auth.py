"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.deps import DB, CurrentTenant
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.app.models.tenant import Tenant
from backend.app.schemas.auth import Token, LoginRequest, RegisterRequest
from backend.app.schemas.tenant import TenantResponse

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(
    request: RegisterRequest,
    db: DB,
):
    """Register a new tenant/user."""
    # Check if email already exists
    result = await db.execute(
        select(Tenant).where(Tenant.email == request.email)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new tenant
    tenant = Tenant(
        email=request.email,
        password_hash=get_password_hash(request.password),
        name=request.name,
    )

    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)

    # Generate tokens
    access_token = create_access_token(subject=tenant.id)
    refresh_token = create_refresh_token(subject=tenant.id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=Token)
async def login(
    request: LoginRequest,
    db: DB,
):
    """Login and get JWT tokens."""
    result = await db.execute(
        select(Tenant).where(Tenant.email == request.email)
    )
    tenant = result.scalar_one_or_none()

    if not tenant or not verify_password(request.password, tenant.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Generate tokens
    access_token = create_access_token(subject=tenant.id)
    refresh_token = create_refresh_token(subject=tenant.id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: DB,
):
    """Refresh access token using refresh token."""
    payload = decode_token(refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    tenant_id = payload.get("sub")
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active == True)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant not found",
        )

    # Generate new tokens
    new_access_token = create_access_token(subject=tenant.id)
    new_refresh_token = create_refresh_token(subject=tenant.id)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=TenantResponse)
async def get_current_user(
    tenant: CurrentTenant,
):
    """Get current authenticated user."""
    return tenant
