from typing import TYPE_CHECKING, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, String, DateTime, Numeric, func, Boolean
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
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    source_app: Mapped[str] = mapped_column(String(50), server_default="posutochka", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Срок жизни бонусов
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True, nullable=False)
    booking_id: Mapped[Optional[int]] = mapped_column(ForeignKey("booking.id"), nullable=True)
    
    # ИСПОЛЬЗУЙ СТРОКУ "Booking" вместо ссылки на класс, чтобы избежать ошибки маппера
    booking: Mapped[Optional["Booking"]] = relationship("Booking", back_populates="coin_transactions") 
    user: Mapped["User"] = relationship(back_populates="coins_transactions")
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
