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

    model_config = {"from_attributes": True}
