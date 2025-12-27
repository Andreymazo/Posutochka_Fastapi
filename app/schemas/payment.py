from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    paid = "paid"
    pending = "pending"
    failed = "failed"


class PaymentBase(BaseModel):
    """Base schema for Payment - common fields."""

    amount: float = Field(..., gt=0)
    payment_status: PaymentStatus


class PaymentCreate(PaymentBase):
    """Schema for creating a new Payment."""

    booking_id: int


class PaymentUpdate(BaseModel):
    """Schema for updating a Payment - all fields optional."""

    amount: float | None = Field(None, gt=0)
    payment_status: PaymentStatus | None = None


class PaymentRead(PaymentBase):
    """Schema for reading Payment data (response)."""

    id: int
    booking_id: int
    payment_date: datetime

    model_config = {"from_attributes": True}
