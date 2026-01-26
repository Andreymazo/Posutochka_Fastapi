from datetime import datetime
import re
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    phone_number: str = Field(..., max_length=15)
    # Добавляем сюда, чтобы они были и в Create, и в Read
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    telegram_username: str | None = Field(None, max_length=32)

class UserCreate(UserBase):
    # Наследуемся от Base, добавляем только пароль
    password: str = Field(..., min_length=6)
    
    # Чтобы ТЕСТЫ не падали прямо сейчас, можно временно сделать так:
    # first_name: str = Field("Имя", min_length=2) 
    # last_name: str = Field("Фамилия", min_length=2)

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean_phone = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^(\+7|7|8)\d{10}$', clean_phone):
            raise ValueError('Номер должен быть в формате +79991112233')
        return clean_phone

    @field_validator('first_name', 'last_name')
    @classmethod
    def capitalize_names(cls, v: str) -> str:
        return v.strip().capitalize()

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = Field(None, max_length=15)
    first_name: str | None = Field(None, min_length=2) # Добавь в Update!
    last_name: str | None = Field(None, min_length=2)
    telegram_username: str | None = Field(None, max_length=32)
    password: str | None = Field(None, min_length=6)

class UserRead(UserBase):
    id: int
    registration_date: datetime
    # Теперь first_name и last_name придут сюда из UserBase автоматически
    telegram_link: str | None = None 
    model_config = ConfigDict(from_attributes=True) # Стиль Pydantic V2
