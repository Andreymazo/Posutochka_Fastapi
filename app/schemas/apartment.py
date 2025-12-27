from pydantic import BaseModel, Field


class ApartmentBase(BaseModel):
    """Base schema for Apartment - common fields."""

    name: str = Field(..., max_length=255)
    description: str | None = None
    price_per_night: float = Field(..., gt=0)
    address: str = Field(..., max_length=255)


class ApartmentCreate(ApartmentBase):
    """Schema for creating a new Apartment."""


class ApartmentUpdate(BaseModel):
    """Schema for updating an Apartment - all fields optional."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    price_per_night: float | None = Field(None, gt=0)
    address: str | None = Field(None, max_length=255)


class ApartmentRead(ApartmentBase):
    """Schema for reading Apartment data (response)."""

    id: int

    model_config = {"from_attributes": True}
