from pydantic import BaseModel, Field


class PhotoBase(BaseModel):
    """Base schema for Photo - common fields."""

    url: str = Field(..., max_length=255)


class PhotoCreate(PhotoBase):
    """Schema for creating a new Photo."""

    apartment_id: int


class PhotoRead(PhotoBase):
    """Schema for reading Photo data (response)."""

    id: int
    apartment_id: int
    is_main: bool 
    model_config = {"from_attributes": True}
