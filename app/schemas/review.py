from datetime import datetime

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    """Base schema for Review - common fields."""

    rating: int = Field(..., ge=1, le=5)
    review: str | None = Field(None, max_length=700)


class ReviewCreate(ReviewBase):
    """Schema for creating a new Review."""

    booking_id: int
    landlord_id: int
    client_id: int
    author_role: str


class ReviewUpdate(BaseModel):
    """Schema for updating a Review - all fields optional."""

    rating: int | None = Field(None, ge=1, le=5)
    review: str | None = Field(None, max_length=700)


class ReviewRead(ReviewBase):
    """Schema for reading Review data (response)."""

    id: int
    booking_id: int
    landlord_id: int
    client_id: int
    author_role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
