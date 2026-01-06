from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.user import User

'''Итоговый счет. Сколько денег сейчас.'''
class Balance(Base):
    """Balance model - represents earnings from bookings."""

    __tablename__ = "balance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Аналог auto_now_add=True (выполняется на стороне БД при вставке)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Аналог auto_now=True (обновляется при каждом UPDATE)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    # Сумма транзакции.
    # precision=12 позволяет хранить миллиарды, scale=2 — копейки
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2), server_default="0.00", 
        nullable=False)
  
    # Foreign keys
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id", ondelete="CASCADE"), nullable=False)    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)

    # Relationships One-to-One модели User поле называется 'balance'
    user: Mapped["User"] = relationship(back_populates="balance")

    def __repr__(self) -> str:
        return f"Balance(id={self.id}, user_id={self.user_id}, amount={self.amount})"
