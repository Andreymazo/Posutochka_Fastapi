from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Owner(Base):
    """Balance model - represents earnings from bookings."""

    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Аналог auto_now_add=True (выполняется на стороне БД при вставке)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Сумма транзакции.
    # precision=10, scale=2 означает 12345678.90 (стандарт для денег)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    # Аналог auto_now=True (обновляется при каждом UPDATE)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Foreign keys
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Relationships
    user: Mapped["User"] = relationship(back_populates="owner")
