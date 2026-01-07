from datetime import datetime
from typing import TYPE_CHECKING
import enum
from sqlalchemy import Enum as SQLEnum, UniqueConstraint
from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.client import Client
    from app.models.landlord import Landlord

class UserRole(enum.Enum):
    CLIENT = "client"
    LANDLORD = "landlord"

"""Rating (new model. OTO (one to one) with Booking OTM (one to many) with Landlord, Client). """
class Review(Base):
    __tablename__ = "rating"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(700), nullable=True)
    author_role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id", ondelete="CASCADE"), nullable=False)
    landlord_id: Mapped[int] = mapped_column(ForeignKey("landlord.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"), nullable=False, index=True)

    # Убрали back_populates к несуществующим полям, оставили только к Booking
    booking: Mapped["Booking"] = relationship(back_populates="reviews") # В Booking должно быть reviews: Mapped[list["Review"]]
    landlord: Mapped["Landlord"] = relationship()
    client: Mapped["Client"] = relationship()

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        UniqueConstraint("booking_id", "author_role", name="uq_booking_author_role"),
    )
# class Review(Base):
#     __tablename__ = "rating"
#     # Чтобы база проверяла диапазон рейтинга (от 1 до 5 звезд)
#     __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),)
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     rating: Mapped[int] = mapped_column(Integer, nullable=False, server_default=None)
#     review: Mapped[str] = mapped_column(String(700), nullable=True, server_default=None)

#       # поле: кто пишет отзыв
#     author_role: Mapped[UserRole] = mapped_column(
#         SQLEnum(UserRole), nullable=False, index=True
#     )

#     # Аналог auto_now_add=True (выполняется на стороне БД при вставке)
#     created_at: Mapped[datetime] = mapped_column(server_default=func.now())

#     # Аналог auto_now=True (обновляется при каждом UPDATE)
#     updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

#     # Forenkeys
   
#     booking_id: Mapped[int] = mapped_column(
#         ForeignKey("booking.id", ondelete="CASCADE"),
#         nullable=False,)
#     landlord_id: Mapped[int] = mapped_column(
#         ForeignKey("landlord.id", ondelete="CASCADE"), nullable=False)
#     client_id: Mapped[int] = mapped_column(
#         ForeignKey("client.id", ondelete="CASCADE"), nullable=False,
#         index=True) # Ускорит выборку всех отзывов конкретного арендодателя

#     # Relationships
#     booking: Mapped["Booking"] = relationship(back_populates="review")
#     landlord: Mapped["Landlord"] = relationship(back_populates="reviews")
#     client: Mapped["Client"] = relationship(back_populates="reviews")

#     __table_args__ = (
#     CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
#     # ГАРАНТИРУЕТ, что один и тот же автор не напишет два отзыва на одну бронь
#     UniqueConstraint("booking_id", "author_role", name="uq_booking_author_role"),
#     )
