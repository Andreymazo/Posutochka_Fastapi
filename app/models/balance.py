from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


if TYPE_CHECKING:
    from app.models.booking import Booking


class Balance(Base):
    """Balance model - represents earnings from bookings."""

    __tablename__ = "balance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Аналог auto_now_add=True (выполняется на стороне БД при вставке)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Сумма транзакции.
    # precision=10, scale=2 означает 12345678.90 (стандарт для денег)
    amount: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    # Аналог auto_now=True (обновляется при каждом UPDATE)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Foreign keys
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    # Отношение Many-to-One: много транзакций баланса могут относиться к одной брони
    booking: Mapped["Booking"] = relationship(back_populates="balances")

    def __repr__(self) -> str:
        return f"Balance(id={self.id}, booking_id={self.booking_id}, amount={self.amount})"