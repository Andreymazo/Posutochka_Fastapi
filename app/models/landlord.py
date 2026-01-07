from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.apartment import Apartment
    from app.models.booking import Booking
    from app.models.review import Review
    from app.models.user import User


class Landlord(Base):
    """Landlord model - represents a property owner."""

    __tablename__ = "landlord"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="landlord")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="landlord")
    apartments: Mapped[list["Apartment"]] = relationship(back_populates="landlord")
    # Разделим отзывы на 2 вида сам и о самом
    # reviews: Mapped[list["Review"]] = relationship(back_populates="landlord")
    # Отзывы, которые оставили КЛИЕНТЫ об этом арендодателе
    reviews_about_me: Mapped[list["Review"]] = relationship(
        "Review",
        primaryjoin="and_(Landlord.id == foreign(Review.landlord_id), Review.author_role == 'CLIENT')",
        viewonly=True,
    )
    # 2. Отзывы, которые САМ арендодатель написал о гостях (его история оценок)
    reviews_i_wrote: Mapped[list["Review"]] = relationship(
        "Review",
        primaryjoin="and_(Landlord.id == foreign(Review.landlord_id), Review.author_role == 'LANDLORD')",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"Landlord(id={self.id}, name='{self.first_name} {self.last_name}')"
