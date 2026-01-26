from __future__ import annotations

from pydantic import BaseModel, Field


from pydantic import BaseModel, ConfigDict, Field
from typing import List

class ClientBase(BaseModel):
    """
    Base schema for Client. 
    Сюда добавляем только специфичные для клиента поля (например, скидки, статус).
    """
    # Если специфичных полей пока нет, класс может быть пустым: pass
    pass

class ClientCreate(ClientBase):
    """Schema for creating a new Client."""
    user_id: int

class ClientUpdate(BaseModel):
    """Schema for updating a Client."""
    # Здесь могут быть поля типа: is_active, preferences и т.д.
    pass

class ClientRead(ClientBase):
    """Schema for reading Client data (response)."""
    id: int
    user_id: int
    
    # В 2026 году принято возвращать либо вложенного юзера, 
    # либо рассчитывать, что фронтенд возьмет ФИО из UserRead
    # reviews_about_me и reviews_i_wrote подтянутся через lazy loading или selectinload
    reviews_about_me: List["ReviewRead"] = []
    reviews_i_wrote: List["ReviewRead"] = []

    model_config = ConfigDict(from_attributes=True)

# Импорты для избежания циклических ссылок
from app.schemas.review import ReviewRead
ClientRead.model_rebuild()
