"""FastAPI dependencies for authentication and database."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.security import decode_token
from backend.app.db.session import get_db, set_tenant_context
from backend.app.models.tenant import Tenant

security = HTTPBearer()


async def get_current_tenant(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Tenant:
    """Get the current authenticated tenant from JWT token."""
    token = credentials.credentials

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_id = payload.get("sub")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_uuid, Tenant.is_active == True)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return tenant


async def get_db_with_tenant(
    tenant: Annotated[Tenant, Depends(get_current_tenant)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncSession:
    """Get database session with tenant context set for RLS."""
    await set_tenant_context(db, str(tenant.id))
    return db


# Type aliases for cleaner dependency injection
CurrentTenant = Annotated[Tenant, Depends(get_current_tenant)]
TenantDB = Annotated[AsyncSession, Depends(get_db_with_tenant)]
DB = Annotated[AsyncSession, Depends(get_db)]
