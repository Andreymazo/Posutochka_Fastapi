from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.apartment import Apartment
    from app.models.balance import Balance
    from app.models.client import Client
    from app.models.landlord import Landlord
    from app.models.payment import Payment
    from app.models.review import Review


class Booking(Base):
    """Booking model - represents a reservation."""

    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    booking_status: Mapped[str] = mapped_column(
        Enum("pending", "confirmed", "cancelled", name="booking_status", create_type=False),
        nullable=False,
    )

    # Foreign keys
    landlord_id: Mapped[int] = mapped_column(
        ForeignKey("landlord.id"), ondelete="CASCADE", nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client.id"), ondelete="CASCADE", nullable=False
    )
    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartment.id"), ondelete="CASCADE", nullable=False
    )

    # Relationships (у брони ОДИН владелец, ОДИН клиент, ОДНА квартира).
    # # Many-to-One: Бронь ссылается на одного родителя
    landlord: Mapped["Landlord"] = relationship(back_populates="bookings")
    client: Mapped["Client"] = relationship(back_populates="bookings")
    apartment: Mapped["Apartment"] = relationship(back_populates="bookings")
    # Отзыв (1-к-1)
    review: Mapped["Review | None"] = relationship(back_populates="booking", uselist=False)

    # One-to-Many: Одна бронь — список платежей и балансовых транзакций
    # В моделях Payment и Balance поле должно называться back_populates="booking"
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")
    balances: Mapped[list["Balance"]] = relationship(back_populates="booking")

    def __repr__(self) -> str:
        return (
            f"Booking(id={self.id}, apartment_id={self.apartment_id}, "
            f"status='{self.booking_status}')"
        )
