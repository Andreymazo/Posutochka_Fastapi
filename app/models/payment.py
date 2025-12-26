from sqlalchemy import Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class Payment(Base):
    """Payment model - represents a booking payment."""
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id"),
        nullable=False
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    payment_status: Mapped[str] = mapped_column(
        Enum("paid", "pending", "failed", name="payment_status"),
        nullable=False
    )

    # Relationships
    booking: Mapped["Booking"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return (
            f"Payment(id={self.id}, booking_id={self.booking_id}, "
            f"amount={self.amount}, status='{self.payment_status}')"
        )
