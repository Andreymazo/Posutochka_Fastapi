from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class OwnerBase(BaseModel):
    """Base schema for Owner - common fields."""
    # Используем Decimal для точности долей, как в модели
    current_share: Decimal = Field(Decimal("0.0000"), ge=0, le=1)
    is_active: bool = True


class OwnerCreate(OwnerBase):
    """Schema for creating a new Owner role."""
    user_id: int
    # booking_id УДАЛЕН, так как роль владельца не привязана к конкретной брони


class OwnerUpdate(BaseModel):
    """Schema for updating an Owner role."""
    current_share: Optional[Decimal] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None


class OwnerRead(OwnerBase):
    """Schema for reading Owner data (response)."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    # В Pydantic v2 используется model_config вместо class Config
    model_config = ConfigDict(from_attributes=True)
