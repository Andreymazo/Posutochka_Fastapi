from __future__ import annotations

from pydantic import BaseModel, Field


class LandlordBase(BaseModel):
    """Base schema for Landlord - common fields."""

    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)


class LandlordCreate(LandlordBase):
    """Schema for creating a new Landlord."""

    user_id: int


class LandlordUpdate(BaseModel):
    """Schema for updating a Landlord - all fields optional."""

    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class LandlordRead(LandlordBase):
    """Schema for reading Landlord data (response)."""

    id: int
    user_id: int
    reviews_about_me: list[ReviewRead] = []
    reviews_i_wrote: list[ReviewRead] = []

    model_config = {"from_attributes": True}


# Import after class definition to avoid circular import
from app.schemas.review import ReviewRead  # noqa: E402

# Rebuild model to resolve forward references
LandlordRead.model_rebuild()
