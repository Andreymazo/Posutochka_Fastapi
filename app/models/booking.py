from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.apartment import Apartment
    from app.models.client import Client
    from app.models.landlord import Landlord
    from app.models.payment import Payment


class Booking(Base):
    """Booking model - represents a reservation."""

    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    booking_status: Mapped[str] = mapped_column(
        Enum("pending", "confirmed", "cancelled", name="booking_status"), nullable=False
    )

    # Foreign keys
    landlord_id: Mapped[int] = mapped_column(ForeignKey("landlord.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"), nullable=False)
    apartment_id: Mapped[int] = mapped_column(ForeignKey("apartment.id"), nullable=False)

    # Relationships
    landlord: Mapped["Landlord"] = relationship(back_populates="bookings")
    client: Mapped["Client"] = relationship(back_populates="bookings")
    apartment: Mapped["Apartment"] = relationship(back_populates="bookings")
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking", uselist=True)

    def __repr__(self) -> str:
        return (
            f"Booking(id={self.id}, apartment_id={self.apartment_id}, "
            f"status='{self.booking_status}')"
        )
