### 1. Общие требования

- **Цель проекта**: Создание платформы для бронирования апартаментов, где пользователи смогут находить и арендовать жилье на короткий срок.
- **Платформа**: Telegram bot для взаимодействия с пользователями.
- **Масштабируемость**: Проект рассчитан на более миллиона пользователей.

### 2. Сущности

#### Пользователь (User)
- **Описание**: Основная сущность для всех типов пользователей.
- **Поля**:
  - ID пользователя (уникальный)
  - Email
  - Номер телефона
  - Пароль (защищенный хэш)
  - Роль (например, "арендодатель", "клиент", "модератор")
  - Дата регистрации
  - `telegram_username` (опциональное поле для Telegram-идентификатора)

#### Арендодатель (Landlord)
- **Описание**: Подкласс пользователя, который предоставляет апартаменты в аренду.
- **Поля**:
  - ID арендодателя (уникальный, ссылается на ID пользователя)
  - Имя
  - Фамилия
  - Профильная фотография

#### Клиент (Client)
- **Описание**: Подкласс пользователя, который арендует апартаменты.
- **Поля**:
  - ID клиента (уникальный, ссылается на ID пользователя)
  - Имя
  - Фамилия

#### Модератор (Moderator)
- **Описание**: Подкласс пользователя, ответственный за управление контентом и бронированиями.
- **Поля**:
  - ID модератора (уникальный, ссылается на ID пользователя)
  - Имя
  - Фамилия

#### Апартамент (Apartment)
- **Описание**: Сущность для описания арендуемых объектов.
- **Поля**:
  - ID апартамента (уникальный)
  - Название
  - Описание
  - Цена за ночь
  - Местоположение
  - Фото (ссылка на список фотографий)

#### Фото (Photo)
- **Описание**: Сущность для хранения изображений апартаментов.
- **Поля**:
  - ID фото (уникальный)
  - ID апартамента (ссылается на ID апартамента)
  - URL фотографии

#### Бронирование (Booking)
- **Описание**: Запись о предстоящей аренде апартаментов.
- **Поля**:
  - ID бронирования (уникальный)
  - ID арендодателя
  - ID клиента
  - ID апартамента
  - Дата начала аренды
  - Дата окончания аренды
  - Стоимость аренды
  - Статус бронирования

#### Оплата (Payment)
- **Описание**: Запись о финансовой транзакции.
- **Поля**:
  - ID платежа (уникальный)
  - ID бронирования
  - Сумма платежа
  - Дата и время оплаты
  - Статус оплаты

### Ключи и связи между сущностями

1. **Пользователь (User)**
   - **ID пользователя** (PK)
   - **Email**, **Номер телефона**
   - **Роль**: `Role` (enum), например, "арендодатель", "клиент", "модератор"

2. **Арендодатель (Landlord)**
   - **ID арендодателя** (PK)
   - **ID пользователя** (FK ссылается на ID пользователя в таблице User)
   - **Имя**, **Фамилия**
   - **Профильная фотография**

3. **Клиент (Client)**
   - **ID клиента** (PK)
   - **ID пользователя** (FK ссылается на ID пользователя в таблице User)
   - **Имя**, **Фамилия**

4. **Модератор (Moderator)**
   - **ID модератора** (PK)
   - **ID пользователя** (FK ссылается на ID пользователя в таблице User)
   - **Имя**, **Фамилия**

5. **Апартамент (Apartment)**
   - **ID апартамента** (PK)
   - **Название**
   - **Описание**
   - **Цена за ночь**
   - **Местоположение**
   - **Список фотографий**: `List<Photo>`, где каждый элемент связан с ID апартамента через FK

6. **Фото (Photo)**
   - **ID фото** (PK)
   - **ID апартамента** (FK ссылается на ID апартамента в таблице Apartment)
   - **URL фотографии**

7. **Бронирование (Booking)**
   - **ID бронирования** (PK)
   - **ID арендодателя** (FK ссылается на ID арендодателя в таблице Landlord)
   - **ID клиента** (FK ссылается на ID клиента в таблице Client)
   - **ID апартамента** (FK ссылается на ID апартамента в таблице Apartment)
   - **Дата начала аренды**
   - **Дата окончания аренды**
   - **Стоимость аренды**
   - **Статус бронирования**

8. **Оплата (Payment)**
   - **ID платежа** (PK)
   - **ID бронирования** (FK ссылается на ID бронирования в таблице Booking)
   - **Сумма платежа**
   - **Дата и время оплаты**
   - **Статус оплаты**

### Логика авторизации

Для реализации логики авторизации можно использовать следующую структуру:

- **Пользователь** (`User`): хранит основные данные пользователя, включая email, номер телефона и пароль.
- **Роль** (`Role`): таблица с возможными ролями пользователей (арендодатель, клиент, модератор).
- **Аутентификация**: при входе проверяется соответствие email/номер телефона и хэша пароля. После успешной аутентификации определяется роль пользователя.
- **Авторизация**: в зависимости от роли пользователя предоставляются различные функции и доступы к системе.

### Технические детали

#### Backend
- **Стек технологий**: FastAPI + SQLAlchemy для Python 
- **База данных**: PostgreSQL с поддержкой асинхронных операций (asyncpg для Python).

#### Frontend
- **Технологии**: Использование Telegram bot API и веб-интерфейса для взаимодействия пользователей.


todo:
+ in aparment key to landlord.  OTM - FK to Landlord.
+ Balance (new model or field in Booking. greater - with Booking.cost)
- Coins (new model. Our currency. Depends on Booking&RaitingLandlord or Booking&RaitingClient)
+ RaitingLandlord (new model. OTM - FK to Landlord. OTM - FK to Client. Greater with new Bookings)
+ Review (new model. OTM - FK to Landlord & OTM - FK to Client).
- make telegram channel Posutochka (functionality not assumed yet)
+ tests (uncomment and refactor)
- map (implement - Apartment.location(s) on it)
- Authorization. Hash passwrd.
+ Owner model. OTO fm Landlord, Client, Owner to Balance.
- Chat
- Notification
- Advertisement.
- Calendar

from typing import Any, List, Optional
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import DATERANGE, ExcludeConstraint
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

class Booking(Base):
    """
    Модель Бронирования — центральный узел системы 'Посуточка'.
    Связывает клиента, арендодателя и объект недвижимости.
    """
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Использование DATERANGE для исключения пересечений на уровне БД
    booking_period: Mapped[Any] = mapped_column(DATERANGE, nullable=False)
    
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
    
    reviews: Mapped[List["Review"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    

    # --- ГИБРИДНЫЕ СВОЙСТВА И ЛОГИКА ---

    @hybrid_property
    def duration_nights(self) -> int:
        """Возвращает количество ночей бронирования."""
        if self.booking_period:
            # В PostgreSQL DATERANGE верхняя граница обычно исключается [)
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
        # GIST индекс для предотвращения пересекающихся дат на одну и ту же квартиру
        ExcludeConstraint(
            ("apartment_id", "="),
            ("booking_period", "&&"),
            name="exclude_overlapping_bookings",
            using="gist",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Booking(id={self.id}, cost={self.cost}, "
            f"period={self.booking_period}, status={self.booking_status})>"
        )