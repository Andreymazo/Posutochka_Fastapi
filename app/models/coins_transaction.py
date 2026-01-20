from typing import TYPE_CHECKING, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, String, DateTime, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.booking import Booking


class CoinsTransaction(Base):
    """
    CoinsTransaction model - represents a single change in user's coin balance.
    Universal for the whole ecosystem (source_app).
    """

    __tablename__ = "coins_transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Сумма транзакции (может быть положительной для кэшбэка и отрицательной для оплаты)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Источник транзакции (например: 'posutochka', 'cleaning', 'referral_system')
    source_app: Mapped[str] = mapped_column(String(50), server_default="posutochka", nullable=False)
    
    # Описание транзакции для пользователя (например: "Кэшбэк за бронирование #55")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    # Связь с бронированием опциональна (нужна только для кэшбэка в Посуточке)
    booking_id: Mapped[Optional[int]] = mapped_column(ForeignKey("booking.id"), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="coins_transactions")
    booking: Mapped[Optional["Booking"]] = relationship()

    def __repr__(self) -> str:
        return f"CoinsTransaction(id={self.id}, amount={self.amount}, user_id={self.user_id})"

# class CoinsTransaction(Base):
#     __tablename__ = "coins_transaction"
    
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("user.id"), index=True)
#     amount = Column(Numeric(10, 2), nullable=False)  # Например, +100.00 или -50.00
    
#     # Источник транзакции (для будущих проектов)
#     source_app = Column(String, default="posutochka") # "rent", "cleaning", "delivery"
    
#     # Описание для пользователя
#     description = Column(String) # "Кэшбэк за бронирование #55"
    
#     # Связь с бронью остается опциональной (nullable=True)
#     booking_id = Column(Integer, ForeignKey("booking.id"), nullable=True)
    
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
