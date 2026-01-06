from datetime import datetime

from pydantic import BaseModel, Field


class OwnerBase(BaseModel):
    """Base schema for Owner - common fields."""

    amount: float = Field(..., gt=0)


class OwnerCreate(OwnerBase):
    """Schema for creating a new Owner."""

    user_id: int
    booking_id: int


class OwnerUpdate(BaseModel):
    """Schema for updating an Owner - all fields optional."""

    amount: float | None = Field(None, gt=0)


class OwnerRead(OwnerBase):
    """Schema for reading Owner data (response)."""

    id: int
    user_id: int
    booking_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
