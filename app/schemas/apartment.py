from geoalchemy2.types import Geography
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.photo import PhotoRead


class ApartmentBase(BaseModel):
    """Base schema for Apartment - common fields."""

    name: str = Field(..., max_length=255)
    description: str | None = None
    price_per_night: float = Field(..., gt=0)
    address: str = Field(..., max_length=255)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ApartmentCreate(ApartmentBase):
    """Schema for creating a new Apartment."""

    location: Geography | None = None


class ApartmentUpdate(BaseModel):
    """Schema for updating an Apartment - all fields optional."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    price_per_night: float | None = Field(None, gt=0)
    address: str | None = Field(None, max_length=255)
    location: Geography | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ApartmentRead(ApartmentBase):
    """Schema for reading Apartment data (response)."""

    id: int
    location: Geography | None = None
    photos: list[PhotoRead] = []

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
