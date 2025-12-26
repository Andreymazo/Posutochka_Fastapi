from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


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
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    cost: Optional[float] = Field(None, gt=0)
    booking_status: Optional[BookingStatus] = None


class BookingRead(BookingBase):
    """Schema for reading Booking data (response)."""
    id: int
    landlord_id: int
    client_id: int
    apartment_id: int

    model_config = {"from_attributes": True}
