from __future__ import annotations


from pydantic import BaseModel, ConfigDict
from typing import List

class LandlordBase(BaseModel):
    """Base schema for Landlord - common fields."""
    # Убрали ФИО, так как они в User. 
    # Здесь можно добавить поля, специфичные только для арендодателя.
    pass

class LandlordCreate(LandlordBase):
    """Schema for creating a new Landlord."""
    user_id: int

class LandlordUpdate(BaseModel):
    """Schema for updating a Landlord - all fields optional."""
    # Если нужно будет обновлять статус (например, 'verified'), добавляй сюда.
    pass

class LandlordRead(LandlordBase):
    """Schema for reading Landlord data (response)."""
    id: int
    user_id: int
    # Поля отзывов подтянутся из связанных моделей
    reviews_about_me: List["ReviewRead"] = []
    reviews_i_wrote: List["ReviewRead"] = []

    model_config = ConfigDict(from_attributes=True)

# Импорт после определения классов для избежания циклических зависимостей
from app.schemas.review import ReviewRead  # noqa: E402

# Пересборка модели для разрешения опережающих ссылок
LandlordRead.model_rebuild()
