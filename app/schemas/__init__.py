# Pydantic Schemas
from app.schemas.apartment import ApartmentBase, ApartmentCreate, ApartmentRead, ApartmentUpdate
from app.schemas.booking import BookingBase, BookingCreate, BookingRead, BookingUpdate
from app.schemas.client import ClientBase, ClientCreate, ClientRead, ClientUpdate
from app.schemas.landlord import LandlordBase, LandlordCreate, LandlordRead, LandlordUpdate
from app.schemas.payment import PaymentBase, PaymentCreate, PaymentRead, PaymentUpdate
from app.schemas.photo import PhotoBase, PhotoCreate, PhotoRead
from app.schemas.user import UserBase, UserCreate, UserRead, UserUpdate

__all__ = [
    "UserBase",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "LandlordBase",
    "LandlordCreate",
    "LandlordRead",
    "LandlordUpdate",
    "ClientBase",
    "ClientCreate",
    "ClientRead",
    "ClientUpdate",
    "ApartmentBase",
    "ApartmentCreate",
    "ApartmentRead",
    "ApartmentUpdate",
    "PhotoBase",
    "PhotoCreate",
    "PhotoRead",
    "BookingBase",
    "BookingCreate",
    "BookingRead",
    "BookingUpdate",
    "PaymentBase",
    "PaymentCreate",
    "PaymentRead",
    "PaymentUpdate",
]
