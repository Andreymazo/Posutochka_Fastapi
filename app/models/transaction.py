import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TransactionType(str, enum.Enum):
    BOOKING_PAYMENT = "booking_payment"  # Клиент оплатил бронь
    BOOKING_INCOME = "booking_income"  # Лендлорд получил деньги
    PLATFORM_COMMISSION = "platform_commission"  # Комиссия сайта (Owner)
    REFUND = "refund"  # Возврат денег клиенту
    WITHDRAWAL = "withdrawal"  # Вывод денег из системы на карту


if TYPE_CHECKING:
    from app.models.balance import Balance
    from app.models.booking import Booking
    from app.models.user import User

"""История платежей"""


class Transaction(Base):
    """История начислений: за какую бронь сколько упало. Фиксирует 
    внутреннее движение средств внутри вашей системы учета 
    (между балансами пользователей - Клиента и Арендодателя)"""

    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Аналог auto_now_add=True (выполняется на стороне БД при вставке)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Аналог auto_now=True (обновляется при каждом UPDATE)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    """: Это сумма, которая зачисляется на баланс конкретного пользователя 
    или списывается с него. Эта сумма может отличаться от суммы amount в Payment"""
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType), nullable=False, index=True
    )
    # Foren keys OTM
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id", ondelete="CASCADE"), nullable=False
    )
    balance_id: Mapped[int] = mapped_column(
        ForeignKey("balance.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    booking: Mapped["Booking"] = relationship(back_populates="transactions")
    user: Mapped["User"] = relationship(back_populates="wallet_history")
    balance: Mapped["Balance"] = relationship(back_populates="transactions")
