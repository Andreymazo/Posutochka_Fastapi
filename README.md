# Posutochka API

API для сервиса аренды квартир (apartment rental service).

## Требования

- Python 3.10+
- PostgreSQL 16+ (или Docker)

## Быстрый старт

### 1. С использованием Docker Compose (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/Andreymazo/Posutochka_Fastapi.git
cd Posutochka_Fastapi

# Запустите PostgreSQL и приложение
docker-compose up -d

# API доступен на http://localhost:8000
# Документация Swagger: http://localhost:8000/docs
```

### 2. Локальная установка

```bash
# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Скопируйте и настройте переменные окружения
cp .env.example .env
# Отредактируйте .env при необходимости

# Запустите PostgreSQL (если не используете Docker)
docker run --name posutochka_postgres \
    -e POSTGRES_PASSWORD=123456 \
    -e POSTGRES_DB=posutochka \
    -d -p 5432:5432 postgres:16

# Примените миграции базы данных
alembic upgrade head

# Запустите сервер разработки
uvicorn app.main:app --reload
```

## Конфигурация

Приложение использует переменные окружения из файла `.env`:

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:123456@localhost:5432/posutochka` |

## API Endpoints

### Основные endpoints

- `GET /` - Приветственное сообщение
- `GET /health` - Проверка состояния
- `GET /docs` - Swagger документация

### Ресурсы

- `/users` - Управление пользователями
- `/landlords` - Управление арендодателями
- `/clients` - Управление клиентами
- `/apartments` - Управление квартирами
- `/photos` - Управление фотографиями
- `/bookings` - Управление бронированиями
- `/payments` - Управление платежами

## Разработка

### Запуск линтера

```bash
pip install ruff
ruff check .
ruff format .
```

### Запуск тестов

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

### Миграции базы данных

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1
```

## Структура проекта

```
posutochka/
├── app/
│   ├── __init__.py
│   ├── main.py           # Точка входа FastAPI
│   ├── database.py       # Конфигурация базы данных
│   ├── models/           # SQLAlchemy модели
│   ├── routers/          # API роутеры
│   └── schemas/          # Pydantic схемы
├── alembic/              # Миграции базы данных
├── tests/                # Тесты
├── .env.example          # Пример конфигурации
├── docker-compose.yml    # Docker Compose конфигурация
├── Dockerfile            # Docker образ
├── requirements.txt      # Python зависимости
└── pyproject.toml        # Конфигурация проекта
```

## Лицензия

MIT

pip install sqlalchemy-postgresql

Please download all logs and data related about the issue to this repository, make sure we compile that data to `./docs/case-studies/issue-{id}` folder, and use it to do deep case study analysis (also make sure to search online for additional facts and data), in which we will reconstruct timeline/sequence of events, find root causes of the problem, and propose possible solutions.


```bash
# Пример команды для установки расширения PostGIS в Docker
docker exec -it containerpostgres psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```
_____________________

https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.validate_assignment

pytest tests/ -v --tb=short --cov=app --cov-report=xml --co
v-report=term
pytest -s tests/test_apartments.py

____________________

# Предполагаем, что у вас уже есть экземпляр сессии db из SessionLocal()

def create_apartment_and_photos(db: Session):
    # Получите первого арендодателя из базы данных
    landlord = db.query(Landlord).first()
    
    if not landlord:
        raise Exception("No landlords found in the database.")
    
    # Создайте апартамент
    apartment_data = {
        "name": "Luxury Penthouse",
        "description": "Spacious penthouse with panoramic city views and modern amenities",
        "price_per_night": 200.0,
        "address": "456 Sky Tower, Saint Petersburg",
        "location": "POINT(30.3351 59.9343)",
        "landlord_id": landlord.id
    }
    db_apartment = Apartment(**apartment_data)
    db.add(db_apartment)
    db.commit()
    
    print(f"Created apartment: id={db_apartment.id}, name='{db_apartment.name}'")
    
    # Создайте первую фотографию апартаментов (living room)
    photo1_data = {
        "url": "https://example.com/apartments/penthouse/living-room.jpg",
        "apartment_id": db_apartment.id
    }
    db_photo1 = Photo(**photo1_data)
    db.add(db_photo1)
    
    # Создайте вторую фотографию апартаментов (bedroom)
    photo2_data = {
        "url": "https://example.com/apartments/penthouse/bedroom.jpg",
        "apartment_id": db_apartment.id
    }
    db_photo2 = Photo(**photo2_data)
    db.add(db_photo2)
    
    db.commit()
    
    print(f"Created photo 1: id={db_photo1.id}, url='{db_photo1.url}'")
    print(f"Created photo 2: id={db_photo2.id}, url='{db_photo2.url}'")

# Вызовите функцию для создания апартаментов и фотографий
create_apartment_and_photos(db)
```

### Важные моменты:

- **Добавление `landlord_id` в миграцию:** Если вы ещё не добавили столбец `landlord_id` в таблицу `apartment`, вам нужно будет создать соответствующую миграцию. Вот пример такой 
миграции:

  ```python
  def upgrade() -> None:
      # ### commands auto generated by Alembic - please adjust! ###
      op.add_column('apartment', sa.Column('landlord_id', sa.Integer(), nullable=True))
      op.create_foreign_key(None, 'apartment', 'landlord', ['landlord_id'], ['id'])
      # ### end Alembic commands ###

  def downgrade() -> None:
      # ### commands auto generated by Alembic - please adjust! ###
      op.drop_constraint(None, 'apartment', type_='foreignkey')
      op.drop_column('apartment', 'landlord_id')
      # ### end Alembic commands ###

______________

Вариант 1: Оставить и Transaction, и Payment (Рекомендуется)
Если Payment используется для фиксации факта оплаты (входящий платеж), а Transaction — это внутренняя запись в балансе (начисление/списание), то они обе нужны.
Вам нужно просто вернуть строку в модель Booking:
python

class Booking(Base):
    """Booking model - represents a reservation."""
    # ... (все остальные поля и импорты) ...

    # One-to-Many: Одна бронь — много транзакций
    # имя атрибута 'transactions' должно совпадать с back_populates в Transaction
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="booking")

    # ДОБАВЬТЕ ЭТУ СТРОКУ НАЗАД:
    # One-to-Many: Одна бронь — много платежей (фактов оплаты)
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")

    def __repr__(self) -> str:
        return (
            f"Booking(id={self.id}, apartment_id={self.apartment_id}, "
            f"status='{self.booking_status}')"
        )

Используйте код с осторожностью.
И убедитесь, что в модели Payment есть зеркальная связь:
python

class Payment(Base):
    # ... (ваши поля в Payment) ...
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id"))
    
    # ЭТО ОБЯЗАТЕЛЬНО:
    booking: Mapped["Booking"] = relationship(back_populates="payments")

Используйте код с осторожностью.
Вариант 2: Использовать только Transaction и удалить Payment
Если вы хотите использовать только Transaction и полностью отказаться от Payment как от отдельной модели, вам нужно найти и удалить файл или класс Payment в вашем проекте, который все еще пытается инициализироваться.
Резюме:
Ошибка исчезнет, как только все back_populates найдут свои парные атрибуты. Вариант 1 — это быстрый и логичный способ исправить проблему, если модель Payment существует.
