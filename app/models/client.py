from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.booking import Booking


class Client(Base):
    """Client model - represents a tenant/guest."""
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        unique=True,
        nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="client")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="client")

    def __repr__(self) -> str:
        return f"Client(id={self.id}, name='{self.first_name} {self.last_name}')"
