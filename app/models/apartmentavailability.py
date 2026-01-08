from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import DATERANGE, Range, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import ExcludeConstraint

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
 
    __table_args__ = (
        # Это ограничение (Constraint) + Индекс (GIST)
        # Оно говорит: "Запрети вставку, если apartment_id совпадает (=) 
        # И blocked_period пересекается (&&)"
        ExcludeConstraint(
            ("apartment_id", "="),
            ("blocked_period", "&&"),
            name="exclude_overlapping_availabilities",
            using="gist",
        ),
    )
