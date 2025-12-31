from geoalchemy2.types import _GISType
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.photo import PhotoRead


# Custom Geography type for Pydantic schema validation
class Geography(_GISType):
    """Custom Geography type that extends GeoAlchemy2's _GISType for Pydantic compatibility."""


class ApartmentBase(BaseModel):
    """Base schema for Apartment - common fields."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    location: Geography
    name: str = Field(..., max_length=255)
    description: str | None = None
    price_per_night: float = Field(..., gt=0)
    address: str = Field(..., max_length=255)


class ApartmentCreate(ApartmentBase):
    """Schema for creating a new Apartment."""


class ApartmentUpdate(BaseModel):
    """Schema for updating an Apartment - all fields optional."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    location: Geography | None = None
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    price_per_night: float | None = Field(None, gt=0)
    address: str | None = Field(None, max_length=255)


class ApartmentRead(ApartmentBase):
    """Schema for reading Apartment data (response)."""

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}

    id: int
    photos: list[PhotoRead] = []
