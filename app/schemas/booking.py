from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.schemas.payment import PaymentRead


class BookingStatus(str, Enum):
    """Booking status enumeration."""

    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class BookingBase(BaseModel):
    """Base schema for Booking - common fields."""

    start_date: date
    end_date: date
    cost: float = Field(..., gt=0)
    booking_status: BookingStatus


class BookingCreate(BookingBase):
    """Schema for creating a new Booking."""

    landlord_id: int
    client_id: int
    apartment_id: int


class BookingUpdate(BaseModel):
    """Schema for updating a Booking - all fields optional."""

    start_date: date | None = None
    end_date: date | None = None
    cost: float | None = Field(None, gt=0)
    booking_status: BookingStatus | None = None


class BookingRead(BookingBase):
    """Schema for reading Booking data (response)."""

    id: int
    landlord_id: int
    client_id: int
    apartment_id: int
    payments: list[PaymentRead] = []

    @model_validator(mode="before")
    @classmethod
    def split_range(cls, data: Any) -> Any:
        """Extract start_date and end_date from booking_period Range object."""
        if hasattr(data, "booking_period") and data.booking_period:
            # Extract boundaries from Postgres Range object
            data.start_date = data.booking_period.lower
            data.end_date = data.booking_period.upper
        return data

    model_config = {"from_attributes": True}
