from typing import TYPE_CHECKING

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.photo import Photo


class Apartment(Base):
    """Apartment model - represents a rental property."""

    __tablename__ = "apartment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    price_per_night: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    # Note: GeoAlchemy2 Geography type can be added when PostGIS is available
    # location: Mapped[Geography] = mapped_column(Geography(geometry_type='POINT', srid=4326))

    # Relationships
    photos: Mapped[list["Photo"]] = relationship(back_populates="apartment")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="apartment")

    def __repr__(self) -> str:
        return (
            f"Apartment(id={self.id}, name='{self.name}', "
            f"price_per_night={self.price_per_night}, address='{self.address}')"
        )
