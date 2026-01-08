"""Schemas for apartment availability management."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, model_validator


class AvailabilityBase(BaseModel):
    """Base schema for ApartmentAvailability - common fields."""

    start_date: date
    end_date: date
    reason: str | None = None
    is_blocked: bool = True
    custom_price: float | None = Field(None, gt=0)
    min_stay_days: int = Field(1, ge=1)


class AvailabilityCreate(AvailabilityBase):
    """Schema for creating a new availability rule."""

    apartment_id: int


class AvailabilityUpdate(BaseModel):
    """Schema for updating an availability rule - all fields optional."""

    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = None
    is_blocked: bool | None = None
    custom_price: float | None = Field(None, gt=0)
    min_stay_days: int | None = Field(None, ge=1)


class AvailabilityRead(AvailabilityBase):
    """Schema for reading availability rule data (response)."""

    id: int
    apartment_id: int

    @model_validator(mode="before")
    @classmethod
    def split_range(cls, data: Any) -> Any:
        """Extract start_date and end_date from blocked_period Range object."""
        if hasattr(data, "blocked_period") and data.blocked_period:
            # Extract boundaries from Postgres Range object
            data.start_date = data.blocked_period.lower
            data.end_date = data.blocked_period.upper
        return data

    model_config = {"from_attributes": True}
