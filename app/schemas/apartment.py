from typing import Annotated, Any

from geoalchemy2.elements import WKBElement
from pydantic import BaseModel, Field, field_validator
from pydantic_shapely import GeometryField
from shapely import wkb, wkt
from shapely.geometry import Point

from app.schemas.photo import PhotoRead


class ApartmentBase(BaseModel):
    """Base schema for Apartment - common fields."""

    location: Annotated[Point, GeometryField()]
    name: str = Field(..., max_length=255)
    description: str | None = None
    price_per_night: float = Field(..., gt=0)
    address: str = Field(..., max_length=255)


class ApartmentCreate(ApartmentBase):
    """Schema for creating a new Apartment."""

    landlord_id: int


class ApartmentUpdate(BaseModel):
    """Schema for updating an Apartment - all fields optional."""

    # model_config = ConfigDict(arbitrary_types_allowed=True)
    # location: Geography
    location: Annotated[Point, GeometryField()]
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    price_per_night: float | None = Field(None, gt=0)
    address: str | None = Field(None, max_length=255)


class ApartmentRead(BaseModel):
    """Schema for reading Apartment data (response)."""

    # model_config = ConfigDict(arbitrary_types_allowed=True)
    location: Annotated[Point, GeometryField()]
    id: int
    name: str
    description: str | None = None
    price_per_night: float
    address: str
    landlord_id: int  # поле для связи с арендодателем

    # Используем аннотацию типа для списка PhotoRead
    photos: list[PhotoRead] = []

    @field_validator("location", mode="before")
    @classmethod
    def handle_dal_types(cls, v: Any) -> Any:
        # 1. Handle WKBElement (coming FROM the database/SQLAlchemy)
        if isinstance(v, WKBElement):
            # Use wkb.loads to convert binary to Shapely Point
            # We use v.data to get the raw binary hex
            return wkb.loads(bytes(v.data))

        # 2. Handle WKT String (for safety/tests)
        if isinstance(v, str) and v.startswith("POINT"):
            return wkt.loads(v)
        return v

    # @field_validator('location', mode='before')
    # @classmethod
    # def parse_location(cls, v: Any) -> Any:

    #     # If the input is a string (like from your fixture), convert it to a Point
    #     if isinstance(v, str) and v.startswith("POINT"):
    #         print('4444444444444444444444444444444444444444444444444444444444444444444444444')
    #         return wkt.loads(v)
    #     return v

    # @field_validator('location', mode='before')
    # @classmethod
    # def handle_dal_types(cls, v: Any) -> Any:
    #     # 1. Handle WKBElement (coming FROM the database/SQLAlchemy)
    #     if isinstance(v, WKBElement):
    #         # Use wkb.loads to convert binary to Shapely Point
    #         # We use v.data to get the raw binary hex
    #         return wkb.loads(bytes(v.data))

    #     # 2. Handle WKT String (for safety/tests)
    #     if isinstance(v, str) and v.startswith("POINT"):
    #         print('4444444444444444444444444444444444444444444444444444444444444444444444443')
    #         return wkt.loads(v)

    #     return v

    # class Config:
    #     from_attributes = True # Ensure Pydantic can read from SQLAlchemy objects
    #     arbitrary_types_allowed = True


# model_config = ConfigDict(arbitrary_types_allowed=True)
# location: Geography
