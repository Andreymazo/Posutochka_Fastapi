from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.review import Review
    from app.models.user import User


class Client(Base):
    """Client model - represents a tenant/guest."""

    __tablename__ = "client"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(), onupdate=func.now())
    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)
    # Relationships
    user: Mapped["User"] = relationship(back_populates="client")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="client")
    # reviews: Mapped[list["Review"]] = relationship(back_populates="client")
    # 1. Отзывы, которые оставили АРЕНДОДАТЕЛИ об этом клиенте (его репутация как гостя)
    # Используем primaryjoin для фильтрации по роли автора
    reviews_about_me: Mapped[list["Review"]] = relationship(
        "Review",
        primaryjoin="and_(Client.id == Review.client_id, Review.author_role == 'LANDLORD')",
        viewonly=True,
        order_by="Review.created_at.desc()",
    )

    # 2. Отзывы, которые САМ клиент написал об объектах/хозяевах (его история отзывов)
    reviews_i_wrote: Mapped[list["Review"]] = relationship(
        "Review",
        primaryjoin="and_(Client.id == Review.client_id, Review.author_role == 'CLIENT')",
        viewonly=True,
        order_by="Review.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"Client(id={self.id}, name='{self.first_name} {self.last_name}')"
