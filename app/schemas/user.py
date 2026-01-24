from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for User - common fields."""

    email: EmailStr
    phone_number: str = Field(..., max_length=15)

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
    # Добавляем поле для ссылки. По умолчанию None, 
    # так как в базе его нет, оно генерируется «на лету».
    telegram_link: str | None = None 
    model_config = {"from_attributes": True}
