from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.payment import PaymentRead


class BookingStatus(str, Enum):
    """Booking status enumeration."""

    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class BookingBase(BaseModel):
    """Base schema for Booking - common fields."""

    start_date: datetime
    end_date: datetime
    cost: float = Field(..., gt=0)
    booking_status: BookingStatus


class BookingCreate(BookingBase):
    """Schema for creating a new Booking."""

    landlord_id: int
    client_id: int
    apartment_id: int


class BookingUpdate(BaseModel):
    """Schema for updating a Booking - all fields optional."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    cost: float | None = Field(None, gt=0)
    booking_status: BookingStatus | None = None


class BookingRead(BookingBase):
    """Schema for reading Booking data (response)."""

    id: int
    landlord_id: int
    client_id: int
    apartment_id: int
    payments: list[PaymentRead] = []

    model_config = {"from_attributes": True}
