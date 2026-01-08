from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import DATERANGE, Range
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.apartment import Apartment


class ApartmentAvailability(Base):
    """Модель настроек календаря для конкретных дат апартамента."""
    __tablename__ = "apartment_availability"

    id: Mapped[int] = mapped_column(primary_key=True)

    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartment.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Период, когда квартира НЕДОСТУПНА
    #  Типизация. Mapped[date] не подходит для диапазона.
    # Используйте Range[date] для корректной работы автодополнения и драйвера psycopg3.
    blocked_period: Mapped[Range[date]] = mapped_column(DATERANGE, nullable=False)

    # Причина блокировки (ремонт, бронь на стороне и т.д.)
    reason: Mapped[str | None] = mapped_column(String(255))
    # 3. Статус блокировки (если True — забронировать нельзя, например, ремонт)
    is_blocked: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    # 4. Цена именно на эту дату (если отличается от базовой цены апартамента)
    # Позволяет делать праздничные наценки или скидки в будни
    custom_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # 5. Минимальный срок аренды (опционально для 2026 года)
    # Например, в праздники можно выставить "минимум 3 ночи"
    min_stay_days: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)

    # Relationships
    apartment: Mapped["Apartment"] = relationship(back_populates="availability_rules")

    # NOTE: GIST exclusion constraint for preventing overlapping availability rules
    # is created via Alembic migration because it requires explicit operator classes
    # (int4_ops for apartment_id, range_ops for blocked_period) which aren't
    # supported by SQLAlchemy's ExcludeConstraint
