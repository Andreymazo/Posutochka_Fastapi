from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from shapely import wkb

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
    # Добавьте поле для объекта Geography
    model_config = {"from_attributes": True}
    location: Geography

    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}

    id: int
    name: str
    description: str | None = None
    price_per_night: float
    address: str
 
    # Используем аннотацию типа для списка PhotoRead
    photos: List[PhotoRead] = []

    

    @field_validator("location", mode="before")
    @classmethod
    def convert_location(cls, v: Any) -> str | None:
        """Convert WKBElement to WKT string."""
        if v is None:
            return None
        # If it's already a string, return as-is
        if isinstance(v, str):
            return v
        # If it's a WKBElement from GeoAlchemy2, convert to WKT
        try:
            # WKBElement has a data attribute containing bytes
            if hasattr(v, "data"):
                geom = wkb.loads(bytes(v.data))
                return geom.wkt
            return str(v)
        except Exception:
            return str(v)
