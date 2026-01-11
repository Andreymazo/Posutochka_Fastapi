import enum
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Используем TYPE_CHECKING, чтобы избежать циклического импорта при инициализации связей
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.owner import Owner
    from app.models.booking import Booking  # Если есть модель бронирования

class OwnerEarning(Base):
    __tablename__ = "owner_earnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    applied_share: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False) 
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Внешние ключи
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id", ondelete="CASCADE"), nullable=False)
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="owner_earnings")
    owner_role: Mapped["Owner"] = relationship(back_populates="owner_earnings")

# class OwnerEarning(Base):
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#      # Полезно сохранить долю, которая была в момент бронирования
#     applied_share: Mapped[Decimal] = mapped_column(Numeric(5, 4)) 
#     created_at: Mapped[datetime] = mapped_column(server_default=func.now())
#     user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
#     owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id")) # Ссылка на роль (для удобства)

#     # Foreign keys
#     booking_id: Mapped[int] = mapped_column(
#         ForeignKey("booking.id", ondelete="CASCADE"), nullable=False
#     )
#     # Связь с пользователем (обязательна для User.owner_earnings)
#     user: Mapped["User"] = relationship(back_populates="owner_earnings")
    
#     # Relationships
#     # user: Mapped["User"] = relationship(back_populates="owner_earnings") # Убрал, т.к. User импортируется
#     # !!! back_populates теперь соответствует имени в модели Owner
#     owner_role: Mapped[Optional["Owner"]] = relationship(back_populates="owner_earnings")
#     amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
   
   

    
