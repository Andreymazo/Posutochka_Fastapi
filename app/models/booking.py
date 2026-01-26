from typing import Any, List, Optional
from decimal import Decimal
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Enum, ForeignKey, Integer, Numeric, DateTime, func, CheckConstraint
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint, Range
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.apartment import Apartment
    from app.models.client import Client
    from app.models.landlord import Landlord
    from app.models.payment import Payment
    from app.models.review import Review
    from app.models.transaction import Transaction
    from app.models.owner_earning import OwnerEarning
    from app.models.message import Message
    from app.models.coins_transaction import CoinsTransaction
    
class Booking(Base):
    """
    Модель Бронирования — центральный узел системы 'Посуточка'.
    Связывает клиента, арендодателя и объект недвижимости.
    """
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Использование DATERANGE для исключения пересечений на уровне БД
    booking_period: Mapped[Range] = mapped_column(DATERANGE, nullable=False)
    
    # Финансовые показатели
    cost: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    
    booking_status: Mapped[str] = mapped_column(
        # Добавил 'completed' и 'refunded' для полноты фин. цикла
        Enum("pending", "confirmed", "cancelled", "completed", "refunded", 
             name="booking_status", create_type=False),
        nullable=False,
        default="pending" # Добавьте дефолтное значение
    )
    # Внешние ключи
    landlord_id: Mapped[int] = mapped_column(
        ForeignKey("landlord.id", ondelete="CASCADE"), nullable=False, index=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client.id", ondelete="CASCADE"), nullable=False, index=True
    )
    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartment.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    landlord: Mapped["Landlord"] = relationship(back_populates="bookings")
    client: Mapped["Client"] = relationship(back_populates="bookings")
    apartment: Mapped["Apartment"] = relationship(back_populates="bookings")
    # легко проверить начисления владельцу прямо из объекта брони:
    owner_earnings: Mapped[List["OwnerEarning"]] = relationship(
    "OwnerEarning", 
    back_populates="booking", 
    cascade="all, delete-orphan"
)

    reviews: Mapped[List["Review"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="booking",cascade="all, delete-orphan" 
    # Если удалим бронь — удаляются все сообщения
    )
    # Связь с транзакциями коинов
    # Это позволит вам делать: booking.coin_transactions
    coin_transactions: Mapped[list["CoinsTransaction"]] = relationship(back_populates="booking")

    # --- ГИБРИДНЫЕ СВОЙСТВА И ЛОГИКА ---

    @hybrid_property
    def duration_nights(self) -> int:
        """Возвращает количество ночей бронирования."""
        if self.booking_period:
            # В PostgreSQL DATERANGE верхняя граница обычно исключается [)возвращает объект Range, у которого есть .lower и .upper
            return (self.booking_period.upper - self.booking_period.lower).days
        return 0
 
    @property
    def total_paid_real(self) -> Decimal:
        """Считает реально поступившие внешние платежи (из модели Payment)."""
        # Важно: p.amount может быть float в вашей модели Payment, 
        # приведение через str гарантирует точность Decimal
        return sum(
            (Decimal(str(p.amount)) for p in self.payments if p.payment_status == "paid"), 
            Decimal("0.00")
        )

    @property
    def is_fully_paid(self) -> bool:
        """Проверка: оплачено ли бронирование полностью для начала распределения прибыли."""
        return self.total_paid_real >= self.cost

    # --- ОГРАНИЧЕНИЯ (CONSTRAINTS) ---

    __table_args__ = (
        # 1. ЗАЩИТА ОТ ОВЕРБУКИНГА:
        # Для одного и того же апартамента (=)
        # периоды дат не должны пересекаться (&&)
        ExcludeConstraint(
            ("apartment_id", "="),
            ("booking_period", "&&"),
            name="exclude_overlapping_bookings",
            using="gist",
        ),
        # 2. ПРОВЕРКА КОРРЕКТНОСТИ ДАТ:
        # Дата заезда всегда строго меньше даты выезда
        CheckConstraint(
            "lower(booking_period) < upper(booking_period)", 
            name="check_booking_dates_order"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Booking(id={self.id}, cost={self.cost}, "
            f"period={self.booking_period}, status={self.booking_status})>"
        )

    # ... (остальное верно) ...

# class Booking(Base):
#     """Booking model - represents a reservation."""

#     __tablename__ = "booking"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     # start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
#     # end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
#     # Вместо start_date и end_date
#     booking_period: Mapped[Any] = mapped_column(DATERANGE, nullable=False)

#     cost: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
#     booking_status: Mapped[str] = mapped_column(
#         Enum("pending", "confirmed", "cancelled", name="booking_status", create_type=False),
#         nullable=False,
#     )

#     # Foreign keys
#     landlord_id: Mapped[int] = mapped_column(
#         ForeignKey("landlord.id", ondelete="CASCADE"), nullable=False
#     )
#     client_id: Mapped[int] = mapped_column(
#         ForeignKey("client.id", ondelete="CASCADE"), nullable=False
#     )
#     apartment_id: Mapped[int] = mapped_column(
#         ForeignKey("apartment.id", ondelete="CASCADE"), nullable=False
#     )

#     # Relationships (у брони ОДИН владелец, ОДИН клиент, ОДНА квартира).
#     # # Many-to-One: Бронь ссылается на одного родителя
#     landlord: Mapped["Landlord"] = relationship(back_populates="bookings")
#     client: Mapped["Client"] = relationship(back_populates="bookings")
#     apartment: Mapped["Apartment"] = relationship(back_populates="bookings")
#     # # Отзыв (1-к-1) Решили сделать двустороннюю возможность отзывы писать
#     # и на клиента тоже, поэтому закоммнтируме пока
#     # review: Mapped["Review | None"] = relationship(back_populates="booking", uselist=False)

#     reviews: Mapped[list["Review"]] = relationship(back_populates="booking")
#     # One-to-Many: Одна бронь — список платежей и балансовых транзакций
#     # В моделях Payment и Balance поле должно называться back_populates="booking"
#     # One-to-Many: Одна бронь — много платежей (фактов оплаты)
#     payments: Mapped[list["Payment"]] = relationship(back_populates="booking")

#     # One-to-Many: Одна бронь — много транзакций
#     # имя атрибута 'transactions' должно совпадать с back_populates в Transaction
#     transactions: Mapped[list["Transaction"]] = relationship(back_populates="booking")

#     # ГИГАНТСКИЙ ПЛЮС: GIST индекс.
#     # Он физически запретит в базе создание пересекающихся броней для одной квартиры.
#     # NOTE: GIST index is created via Alembic migration (not here) because it requires
#     # explicit operator classes (int4_ops, range_ops) which aren't supported by SQLAlchemy Index

#     __table_args__ = (
#         ExcludeConstraint(
#             ("apartment_id", "="),
#             ("booking_period", "&&"),
#             name="exclude_overlapping_bookings",
#             using="gist",
#         ),
#     )
#     def __repr__(self) -> str:
#         return (
#             f"Booking(id={self.id}, apartment_id={self.apartment_id}, "
#             f"status='{self.booking_status}')"
#         )


# Важное примечание для миграций (2026):
# Когда вы будете создавать миграцию через Alembic, вам нужно будет вручную добавить команду для расширения btree_gist, иначе индекс не создастся. В файле миграции добавьте:
# python

# def upgrade():
#     op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')
#     # ... остальной код миграции

# какие еще изменения потребуются в связи с использованием DATERANGE
# Думаю…
# Использование
# DATERANGE — это мощное решение, но оно меняет способ взаимодействия с данными
#  на всех уровнях: от базы до фронтенда. Вот список изменений, которые потребуются в 2026 году:
# 1. Изменение в логике создания бронирования (Python)
# Вы больше не передаете две даты. Вам нужно использовать объект Range из библиотеки psycopg
#  (или sqlalchemy.dialects.postgresql).
# Было: Booking(start_date=d1, end_date=d2, ...)
# Стало:
# python

# from sqlalchemy.dialects.postgresql import Range

# # [) означает: дата заезда включена, дата выезда — нет (стандарт отелей)
# period = Range(start_date, end_date, bounds="[)")
# new_booking = Booking(booking_period=period, ...)

# Используйте код с осторожностью.
# 2. Поиск доступности (Самое важное изменение)
# Запросы на поиск свободных квартир теперь пишутся через операторы пересечения. В SQL это
# оператор &&, в SQLAlchemy — метод .overlaps().
# Запрос "Найти квартиры, которые ЗАНЯТЫ в эти даты":
# python

# search_range = Range(check_in, check_out, bounds="[)")
# query = select(Booking.apartment_id).where(
#     Booking.booking_period.overlaps(search_range)
# )

# Используйте код с осторожностью.
# 3. Изменения в Pydantic-схемах
# Поскольку DATERANGE — это специфический тип Postgres, Pydantic не умеет его "готовить" из коробки.
#  Вам придется либо разбирать его в GetterDict, либо оставить в схемах два поля
# (start_date, end_date), а в модель базы данных превращать их в Range на уровне сервиса.
# Рекомендуемая схема:
# python

# class BookingResponse(BaseModel):
#     id: int
#     start_date: date
#     end_date: date

#     @model_validator(mode='before')
#     @classmethod
#     def split_range(cls, data: Any):
#         if hasattr(data, 'booking_period'):
#             # Извлекаем границы из Range объекта Postgres
#             data.start_date = data.booking_period.lower
#             data.end_date = data.booking_period.upper
#         return data

# Используйте код с осторожностью.
# 4. Настройка Alembic (Миграции)
# Как я упоминал ранее, GIST индекс по датам не заработает в Postgres без расширения. Вам нужно добавить в миграцию:
# python

# def upgrade():
#     # Без этого расширения миграция упадет на создании индекса
#     op.execute('CREATE EXTENSION IF NOT EXISTS btree_gist')

# Используйте код с осторожностью.
# 5. Получение дат для фронтенда
# Фронтенд (React/Vue) всё равно захочет получить две строки или два объекта даты.
# В SQLAlchemy 2.0 при выборке вы сможете обращаться к атрибутам:

#     booking.booking_period.lower — вернет дату заезда.
#     booking.booking_period.upper — вернет дату выезда.

# 6. Расчет стоимости
# Если раньше вы считали (end_date - start_date).days * price, то теперь:
# python

# # В Postgres Range разница дат считается так:
# days = booking.booking_period.upper - booking.booking_period.lower
# total_cost = days.days * daily_price

# Используйте код с осторожностью.
# Итог:
# Главное изменение — ментальное. Вы перестаете думать о двух независимых
# колонках и начинаете воспринимать бронь как единый неизменяемый отрезок
# времени. Это избавляет вас от багов типа "дата выезда раньше даты заезда"
# еще на уровне архитектуры. [1][2]
