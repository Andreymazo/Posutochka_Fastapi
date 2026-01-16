from typing import TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking


class Payment(Base):
    """Payment model - represents a booking payment.запись о внешнем событии оплаты"""

    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    amount: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    payment_status: Mapped[str] = mapped_column(
        Enum("paid", "pending", "failed", name="payment_status", create_type=False),
        nullable=False,
    )
    # Foreign keys
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id"), nullable=False)
    # Relationships
    booking: Mapped["Booking"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return (
            f"Payment(id={self.id}, booking_id={self.booking_id}, "
            f"amount={self.amount}, status='{self.payment_status}')"
        )
