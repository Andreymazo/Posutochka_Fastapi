from pydantic import BaseModel, Field
from geoalchemy2.types import Geography
from app.schemas.photo import PhotoRead
from typing import List

class ApartmentBase(BaseModel):
    """Base schema for Apartment - common fields."""

    name: str = Field(..., max_length=255)
    description: str | None = None
    price_per_night: float = Field(..., gt=0)
    address: str = Field(..., max_length=255)
    location: Geography 
    # Используйте строковый тип для хранения координат в формате WKT
    # location_wkt: str 

    # model_config = {
    #        "arbitrary_types_allowed": True,
    #    }


class ApartmentCreate(ApartmentBase):
    """Schema for creating a new Apartment."""

     # Пример использования при сохранении в базу данных
    # def save_apartment_to_db(apartment: ApartmentBase) -> None:
    #     # Преобразуйте строку WKT в объект Geography перед сохранением
    #     apartment_dict = apartment.dict()
    #     if 'location_wkt' in apartment_dict:
    #         apartment_dict['location'] = GeoTypes.Geography.from_wkt(apartment_dict.pop('location_wkt'))
    #     # Сохраните в базу данных, используя SQLAlchemy или другой ORM

class ApartmentUpdate(BaseModel):
    """Schema for updating an Apartment - all fields optional."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    price_per_night: float | None = Field(None, gt=0)
    address: str | None = Field(None, max_length=255)
    location: Geography 
    #     location_wkt: str
 


class ApartmentRead(ApartmentBase):
    """Schema for reading Apartment data (response)."""
    # Добавьте поле для объекта Geography
    location: Geography

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     if 'location_wkt' in kwargs:
    #         self.location = Geography.from_wkt(kwargs['location_wkt'])
   


    # id: int
    # # Используем аннотацию типа для списка PhotoRead
    # photos: list["PhotoRead"]


    # model_config = {"from_attributes": True}
    id: int
    name: str
    description: str | None = None
    price_per_night: float
    address: str
    # location: str
    # Используем аннотацию типа для списка PhotoRead
    photos: List[PhotoRead] = []

    model_config = {"from_attributes": True}

