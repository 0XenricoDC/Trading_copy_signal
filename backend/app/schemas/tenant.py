"""Tenant schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from backend.app.models.tenant import SubscriptionTier


class TenantBase(BaseModel):
    """Base tenant schema."""

    email: EmailStr
    name: str | None = None


class TenantCreate(TenantBase):
    """Schema for creating a tenant."""

    password: str


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: str | None = None
    email: EmailStr | None = None


class TenantResponse(TenantBase):
    """Schema for tenant response."""

    id: UUID
    subscription_tier: SubscriptionTier
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantInDB(TenantResponse):
    """Schema for tenant in database (includes hashed password)."""

    password_hash: str
