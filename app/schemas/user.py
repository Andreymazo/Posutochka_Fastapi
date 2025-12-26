from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    landlord = "landlord"
    client = "client"


class UserBase(BaseModel):
    """Base schema for User - common fields."""
    email: EmailStr
    phone_number: str = Field(..., max_length=15)
    role: UserRole
    telegram_username: Optional[str] = Field(None, max_length=32)


class UserCreate(UserBase):
    """Schema for creating a new User."""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema for updating a User - all fields optional."""
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=15)
    telegram_username: Optional[str] = Field(None, max_length=32)
    password: Optional[str] = Field(None, min_length=6)


class UserRead(UserBase):
    """Schema for reading User data (response)."""
    id: int
    registration_date: datetime

    model_config = {"from_attributes": True}
