from pydantic import BaseModel, Field, ConfigDict
from geoalchemy2.types import Geography, _GISType
from app.schemas.photo import PhotoRead
from typing import List

# This is not a pydantic model, it's an arbitrary class
class Geography(_GISType):
    pass
class ApartmentBase(BaseModel):
    """Base schema for Apartment - common fields."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    location: Geography 
    
    name: str = Field(..., max_length=255)
    description: str | None = None
    price_per_night: float = Field(..., gt=0)
    address: str = Field(..., max_length=255)
    

class ApartmentCreate(ApartmentBase):
    """Schema for creating a new Apartment."""


class ApartmentUpdate(BaseModel):
    """Schema for updating an Apartment - all fields optional."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    location: Geography 
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    price_per_night: float | None = Field(None, gt=0)
    address: str | None = Field(None, max_length=255)
     

class ApartmentRead(ApartmentBase):
    """Schema for reading Apartment data (response)."""
    # Добавьте поле для объекта Geography
    model_config = {"from_attributes": True}
    location: Geography
   
    id: int
    name: str
    description: str | None = None
    price_per_night: float
    address: str
    # Используем аннотацию типа для списка PhotoRead
    photos: List[PhotoRead] = []

    

