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

________________________
>>> (posutochka_fasapi) andreymazo@andreymazo-GF63-Thin-11UC:~/Projects/Posutochka$ alembic revision --autogenerate -m "add geofield to Apartaments"
... INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
... INFO  [alembic.runtime.migration] Will assume transactional DDL.
... INFO  [alembic.autogenerate.compare] Detected removed table 'spatial_ref_sys'
... INFO  [alembic.ddl.postgresql] Detected sequence named 'booking_id_seq' as owned by integer column 'booking(id)', assuming SERIAL and omitting
... INFO  [alembic.ddl.postgresql] Detected sequence named 'payment_id_seq' as owned by integer column 'payment(id)', assuming SERIAL and omitting
... INFO  [alembic.ddl.postgresql] Detected sequence named 'photo_id_seq' as owned by integer column 'photo(id)', assuming SERIAL and omitting
...   Generating /home/andreymazo/Projects/Posutochka/alembic/versions/bcc1ae1d607f_add_geofield_to_apartaments.py ...  done миграция def upgrade():
...     if not column_exists('apartment', 'location'):
...         print('1111111111111111111111111111111111111111111111100')
...         # Добавляем колонку location, если она не существует
...         op.add_column(
...             'apartment',
...             sa.Column('location', 
...                       Geography(geometry_type='POINT', srid=4326, dimension=2),
...                       nullable=False)
...         )
... 
...     if not index_exists('apartment', 'idx_apartment_location'):
...         # Создаем индекс idx_apartment_location, если он не существует
...         op.create_index(
...             'idx_apartment_location',
...             'apartment',
...             ['location'],
...             unique=False,
...             postgresql_using='gist'
...         ) проходит, но в таблице apartment поле location не создается
Проблема может быть связана с тем, что вы пытаетесь использовать тип `Geography` напрямую без правильного импорта. Также стоит убедиться, что вы используете правильный модуль для 
определения географического типа данных.

В SQLAlchemy и Alembic, типы данных географии обычно определяются через специальный пакет `sqlalchemy_postgis`. Убедитесь, что этот пакет установлен в вашем окружении. Если он не 
установлен, вы можете установить его с помощью pip:

```bash
pip install sqlalchemy-postgresql
```

Теперь давайте исправим ваш код для использования правильного типа данных географии.

1. Импортируйте необходимые модули.
2. Убедитесь, что тип данных `Geography` определен правильно.

Вот как должен выглядеть ваш файл миграции:

```python
from alembic import op
import sqlalchemy as sa

# Импорт PostGIS типа данных для географии
from sqlalchemy.dialects.postgresql import GEOGRAPHY

def upgrade():
    # Проверяем наличие колонки location в таблице apartment
    if not op column_exists('apartment', 'location'):
        print('1111111111111111111111111111111

>>> продолжай
Извините за недочет в предыдущем ответе. Давайте исправим и завершим код миграции, убедившись, что мы правильно импортируем тип данных `Geography` из модуля 
`sqlalchemy.dialects.postgresql`.

Вот как должен выглядеть ваш файл миграции:

```python
from alembic import op
import sqlalchemy as sa

# Импортируем необходимый тип данных для географии
from sqlalchemy.dialects.postgresql import GEOGRAPHY

def column_exists(table_name, column_name):
    # Получаем текущее соединение из контекста Alembic
    bind = op.get_context().bind
    # Создаем инспектор для базы данных
    insp = sa.inspect(bind)
    # Получаем список колонок для указанной таблицы
    columns = insp.get_columns(table_name)
    # Проверяем наличие колонки по имени
    return any(c["name"] == column_name for c in columns)

def index_exists(table_name, index_name):
    bind = op.get_context().bind
    insp = sa.inspect(bind)
    indexes = insp.get_indexes(table_name)
    return any(index['name'] == index_name for index in indexes)

def upgrade():
    # Проверяем существование колонки location в таблице apartment
    if not column_exists('apartment', 'location'):
        print('Добавление колонки location...')
        # Добавляем колонку location, если она не существует
        op.add_column(
            'apartment',
            sa.Column('location', 
                      GEOGRAPHY(geometry_type='POINT', srid=4326, dimension=2),
                      nullable=False)
        )

    if not index_exists('apartment', 'idx_apartment_location'):
        print('Создание индекса idx_apartment_location...')
        # Создаем индекс idx_apartment_location, если он не существует
        op.create_index(
            'idx_apartment_location',
            'apartment',
            ['location'],
            unique=False,
            postgresql_using='gist'
        )

def downgrade():
    if column_exists('apartment', 'location'):
        print('Удаление колонки location...')
        # Удаляем колонку location, если она существует
        op.drop_column('apartment', 'location')

    if index_exists('apartment', 'idx_apartment_location'):
        print('Удаление индекса idx_apartment_location...')
        # Удаляем индекс idx_apartment_location, если он существует
        op.drop_index('idx_apartment_location', table_name='apartment')
```

### Дополнительные изменения:

1. **Импорт `GEOGRAPHY`:** 
   - Используйте правильный импорт из `sqlalchemy.dialects.postgresql`. В моем предыдущем ответе была ошибка в синтаксисе, которая должна быть исправлена.

2. **Проверка на существование:**
   - Убедитесь, что функции `column_exists` и `index_exists` работают правильно. Я добавил некоторые диагностические сообщения для отладки, чтобы увидеть, какие шаги выполняются.

3. **Тип данных географии:**
   - Используйте `GEOGRAPHY(geometry_type='POINT', srid=4326, dimension=2)` вместо `Geography`.

### Установка PostGIS:

Убедитесь, что у вас установлен PostGIS на вашей базе данных. Если вы используете Docker или контейнеры, проверьте конфигурацию вашего образа PostgreSQL.

```bash
# Пример команды для установки расширения PostGIS в Docker
docker exec -it your-postgres-container psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

После выполнения этих изменений, попробуйте снова сгенерировать миграцию и применить её к вашей базе данных.

_____________________