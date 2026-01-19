from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, String, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.balance import Balance
    from app.models.client import Client
    from app.models.landlord import Landlord
    from app.models.owner import Owner
    from app.models.transaction import Transaction
    from app.models.investor import Investor
    from app.models.owner_earning import OwnerEarning
    from app.models.message import Message

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    

    # РОЛИ (One-to-One)
    landlord: Mapped[Optional["Landlord"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    client: Mapped[Optional["Client"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    balance: Mapped[Optional["Balance"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    investor: Mapped[Optional["Investor"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    owner: Mapped[Optional["Owner"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # Аналог auto_now_add=True (выполняется на стороне БД при вставке)
    registration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Аналог auto_now=True (обновляется при каждом UPDATE)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    telegram_username: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # ИСТОРИЯ (One-to-Many)
    wallet_history: Mapped[list["Transaction"]] = relationship(back_populates="user")
    owner_earnings: Mapped[list["OwnerEarning"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    # Коллекция всех сообщений, которые отправил этот пользователь
    sent_messages: Mapped[list["Message"]] = relationship(back_populates="sender")
    # Добавьте это:
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)

    def __repr__(self) -> str:
        return f"User(id={self.id}, email='{self.email}')"

# class User(Base):
#     """User model - base entity for authentication and authorization."""

#     __tablename__ = "user"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    # password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # # registration_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # registration_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    # telegram_username: Mapped[str | None] = mapped_column(String(32), nullable=True)

#     # Relationships - One-to-One
#     landlord: Mapped[Optional["Landlord"]] = relationship(
#         back_populates="user", uselist=False, cascade="all, delete-orphan"
#     )
#     client: Mapped[Optional["Client"]] = relationship(
#         back_populates="user", uselist=False, cascade="all, delete-orphan"
#     )
  
#     balance: Mapped[Optional["Balance"]] = relationship(
#         back_populates="user", uselist=False, cascade="all, delete-orphan"
#     )
  
#     investor: Mapped[Optional["Investor"]] = relationship(
#         back_populates="user", uselist=False, cascade="all, delete-orphan"
#     )
#     # Ссылка на роль (соучредитель или нет)
#     owner: Mapped[Optional["Owner"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
#     wallet_history: Mapped[list["Transaction"]] = relationship(back_populates="user")
    
#     # Ссылка на историю всех заработанных денег Влыдельца
#     owner_earnings: Mapped[list["OwnerEarning"]] = relationship(back_populates="user", cascade="all, delete-orphan")
#     def __repr__(self) -> str:
#         return f"User(id={self.id}, email='{self.email}')"
