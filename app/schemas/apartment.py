from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.photo import PhotoRead


class ApartmentBase(BaseModel):
    """Base schema for Apartment - common fields."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., max_length=255)
    description: str | None = None
    price_per_night: float = Field(..., gt=0)
    address: str = Field(..., max_length=255)
    location: str = Field(..., description="Location in WKT format, e.g., 'POINT(lon lat)'")


class ApartmentCreate(ApartmentBase):
    """Schema for creating a new Apartment."""


class ApartmentUpdate(BaseModel):
    """Schema for updating an Apartment - all fields optional."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    price_per_night: float | None = Field(None, gt=0)
    address: str | None = Field(None, max_length=255)
    location: str | None = Field(None, description="Location in WKT format, e.g., 'POINT(lon lat)'")


class ApartmentRead(BaseModel):
    """Schema for reading Apartment data (response)."""

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}

    id: int
    name: str
    description: str | None = None
    price_per_night: float
    address: str
    location: Any = None  # Use Any to handle Geography type from database
    photos: list[PhotoRead] = []
