from typing import TYPE_CHECKING

import sqlalchemy.ext.compiler
from geoalchemy2.types import Geography
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# Compile Geography to TEXT for SQLite (for testing without PostGIS)
@sqlalchemy.ext.compiler.compiles(Geography, "sqlite")
def _compile_geography_sqlite(_element, _compiler, **_kw):
    """Compile Geography type to TEXT for SQLite."""
    return "TEXT"


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
    # Note: GeoAlchemy2 Geography type requires PostGIS - compiles to TEXT for SQLite tests
    # spatial_index=False disables spatial index creation which requires SpatiaLite
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=True
    )

    # Relationships
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="apartment", cascade="all, delete-orphan", uselist=True
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="apartment", uselist=True)

    def __repr__(self) -> str:
        return (
            f"Apartment(id={self.id}, name='{self.name}', "
            f"price_per_night={self.price_per_night}, address='{self.address}')"
        )
