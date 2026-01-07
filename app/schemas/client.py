from __future__ import annotations

from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    """Base schema for Client - common fields."""

    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)


class ClientCreate(ClientBase):
    """Schema for creating a new Client."""

    user_id: int


class ClientUpdate(BaseModel):
    """Schema for updating a Client - all fields optional."""

    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class ClientRead(ClientBase):
    """Schema for reading Client data (response)."""

    id: int
    user_id: int
    reviews_about_me: list[ReviewRead] = []
    reviews_i_wrote: list[ReviewRead] = []

    model_config = {"from_attributes": True}


# Import after class definition to avoid circular import
from app.schemas.review import ReviewRead  # noqa: E402

# Rebuild model to resolve forward references
ClientRead.model_rebuild()
