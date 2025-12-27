from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration."""

    landlord = "landlord"
    client = "client"


class UserBase(BaseModel):
    """Base schema for User - common fields."""

    email: EmailStr
    phone_number: str = Field(..., max_length=15)
    role: UserRole
    telegram_username: str | None = Field(None, max_length=32)


class UserCreate(UserBase):
    """Schema for creating a new User."""

    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema for updating a User - all fields optional."""

    email: EmailStr | None = None
    phone_number: str | None = Field(None, max_length=15)
    telegram_username: str | None = Field(None, max_length=32)
    password: str | None = Field(None, min_length=6)


class UserRead(UserBase):
    """Schema for reading User data (response)."""

    id: int
    registration_date: datetime

    model_config = {"from_attributes": True}
