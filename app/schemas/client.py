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

    model_config = {"from_attributes": True}
