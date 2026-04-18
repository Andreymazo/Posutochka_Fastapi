from datetime import date
from enum import Enum
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator

from app.schemas.payment import PaymentRead


class BookingStatus(str, Enum):
    """Booking status enumeration."""

    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class BookingBase(BaseModel):
    """Base schema for Booking - common fields."""

    check_in: date
    check_out: date
    cost: float = Field(..., gt=0)
    booking_status: BookingStatus


class BookingCreate(BookingBase):
    apartment_id: int
    check_in: date
    check_out: date
  
    @model_validator(mode='after')
    def check_dates(self) -> Self:
        if self.check_out <= self.check_in:
            raise ValueError("Дата выезда должна быть позже даты заезда")
        return self


class BookingUpdate(BaseModel):
    """Schema for updating a Booking - all fields optional."""

    check_in: date | None = None
    check_out: date | None = None
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
            data.check_in = data.booking_period.lower
            data.check_out = data.booking_period.upper
        return data

    model_config = {"from_attributes": True}
