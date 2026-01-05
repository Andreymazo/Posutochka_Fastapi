from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Integer, Float, String, func, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.landlord import Landlord
    from app.models.client import Client
    

'''Rating (new model. OTO (one to one) with Booking OTM (one to many) with Landlord, Client). '''
class Review(Base):
    __tablename__ = "rating"
      # Чтобы база проверяла диапазон рейтинга (от 1 до 5 звезд)
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, server_default=None)
    review: Mapped[str] = mapped_column(String(700), nullable=True, server_default=None)
    # Аналог auto_now_add=True (выполняется на стороне БД при вставке)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Аналог auto_now=True (обновляется при каждом UPDATE)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(),onupdate=func.now())
    
    # Forenkeys
      # Чтобы сделать One-to-One с Booking на уровне базы, добавляем unique=True
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True  # ГАРАНТИРУЕТ, что для одной брони будет только ОДИН отзыв
    )
    landlord_id: Mapped[int] = mapped_column(ForeignKey("landlord.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    booking: Mapped["Booking"] = relationship(back_populates="review")
    landlord: Mapped["Landlord"] = relationship(back_populates="reviews")
    client: Mapped["Client"] = relationship(back_populates="reviews")