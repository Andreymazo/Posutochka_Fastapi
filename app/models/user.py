from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.landlord import Landlord


class User(Base):
    """User model - base entity for authentication and authorization."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    telegram_username: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Relationships - One-to-One
    landlord: Mapped[Optional["Landlord"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    client: Mapped[Optional["Client"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email='{self.email}')"
