from decimal import Decimal
from typing import TYPE_CHECKING

from geoalchemy2.types import Geography
from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.apartmentavailability import ApartmentAvailability
    from app.models.booking import Booking
    from app.models.landlord import Landlord
    from app.models.photo import Photo


class Apartment(Base):
    """Apartment model - represents a rental property."""

    __tablename__ = "apartment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    # Рекомендуется Numeric для точности цен
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)

    address: Mapped[str] = mapped_column(String(255), nullable=False)
    # Note: GeoAlchemy2 Geography type can be added when PostGIS is available
    location: Mapped[Geography] = mapped_column(Geography(geometry_type="POINT", srid=4326))

    # Relationships
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="apartment", cascade="all, delete-orphan"
    )
    # Бронирования: список всех броней этой квартиры
    bookings: Mapped[list["Booking"]] = relationship(back_populates="apartment")
    # Один владелец у одной квартиры, но в Landlord - apartments - список:
    landlord: Mapped["Landlord"] = relationship(back_populates="apartments")
    # Взаимосвязь с правилами доступности и цен
    # Указываем lazy="selectin" для эффективной подгрузки в асинхронных запросах
    availability_rules: Mapped[list["ApartmentAvailability"]] = relationship(
        back_populates="apartment",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Foreign Keys
    landlord_id: Mapped[int] = mapped_column(
        ForeignKey("landlord.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"Apartment(id={self.id}, name='{self.name}', "
            f"price_per_night={self.price_per_night}, address='{self.address}')"
        )
