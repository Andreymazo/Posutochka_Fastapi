# Posutochka API

API для сервиса краткосрочной аренды квартир (apartment rental service).

## Требования

- **Python** 3.10+
- **PostgreSQL** 16+ (с расширением PostGIS)
- **Redis** 7+ (для брокеров задач и кеширования)
- **MinIO** (для хранения медиа-файлов)

## Быстрый старт

### 1. С использованием Docker Compose (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com
cd Posutochka_Fastapi

# Запустите всю инфраструктуру (БД, Redis, MinIO, FastAPI, Celery)
docker compose up -d

# API доступен на http://localhost:8000
# Документация Swagger: http://localhost:8000/docs
# Панель MinIO: http://localhost:9001
```

### 2. Локальная установка для разработки

```bash
# Создайте и активируйте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env при необходимости

# Запустите базу данных PostgreSQL c PostGIS в Docker
docker run --name containerpostgres \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=123456 \
    -e POSTGRES_DB=posutochka \
    -d -p 5434:5432 postgis/postgis:16-3.4

# Инициализируйте расширения в БД
docker exec -it containerpostgres psql -U postgres -d posutochka -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS btree_gist;"

# Примените миграции Alembic
alembic upgrade head

# Запустите сервер разработки
uvicorn app.main:app --reload
```

## Конфигурация

Приложение настраивается через переменные окружения в файле `.env`:

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `DATABASE_URL` | Строка подключения к PostgreSQL | `postgresql://postgres:123456@localhost:5432/posutochka` |

## Структура проекта

```text
posutochka/
├── app/                        # Основной код приложения FastAPI
│   ├── main.py                 # Точка входа в API, инициализация приложения
│   ├── database.py             # Настройка подключения к БД и сессий SQLAlchemy
│   ├── config.py               # Валидация и чтение переменных окружения (.env)
│   ├── models/                 # SQLAlchemy модели базы данных
│   │   ├── __init__.py
│   │   ├── user.py             # Модели пользователей (Client, Landlord, User)
│   │   ├── apartment.py        # Модели квартир и гео-данных (PostGIS)
│   │   └── booking.py          # Модели бронирований и статусов
│   ├── routers/                # Эндпоинты API (Маршрутизация)
│   │   ├── auth.py             # Авторизация, регистрация и JWT токены
│   │   ├── users.py            # Управление пользователями
│   │   ├── apartments.py       # Поиск и создание объектов недвижимости
│   │   └── bookings.py         # Логика бронирования квартир
│   ├── schemas/                # Pydantic-схемы для валидации запросов и ответов
│   │   ├── user.py
│   │   ├── apartment.py
│   │   └── booking.py
│   └── services/               # Бизнес-логика приложения
│       ├── auth.py             # Хеширование паролей, генерация токенов
│       └── storage.py          # Интеграция с MinIO для загрузки фотографий
├── alembic/                    # Миграции базы данных Alembic
│   ├── versions/               # Файлы сгенерированных миграций
│   └── env.py                  # Конфигурация окружения Alembic для работы с моделями
├── tests/                      # Автоматические тесты (pytest)
│   ├── conftest.py             # Фикстуры для тестов (тестовая БД, сессии, клиенты)
│   ├── test_auth.py            # Тесты эндпоинтов авторизации
│   ├── test_users.py           # Тесты управления пользователями
│   └── test_bookings.py        # Тесты бизнес-логики бронирования
├── scripts/                    # Вспомогательные скрипты
│   └── seed_apartm.py          # Скрипт для наполнения БД тестовыми квартирами
├── .env.example                # Пример файла с переменными окружения
├── .gitignore                  # Список исключений для Git
├── Dockerfile                  # Инструкции для сборки Docker-образа бэкенда
├── docker-compose.yml          # Манифест для запуска всей инфраструктуры проекта
├── pyproject.toml              # Конфигурация инструментов разработки (Ruff, Pytest)
└── requirements.txt            # Список зависимостей Python-приложения
```


## Разработка и тестирование

### Линтинг и форматирование (Ruff)
```bash
pip install ruff
ruff check .      # Проверка кода
ruff format .     # Форматирование кода
```

### Запуск тестов (Pytest)
```bash
pip install pytest pytest-asyncio httpx pytest-cov
pytest tests/ -v --tb=short
```

### Миграции базы данных (Alembic)
```bash
# Создать новую миграцию автоматически на основе моделей
alembic revision --autogenerate -m "описание_изменений"

# Применить все актуальные миграции
alembic upgrade head

# Откатить последнюю миграцию на 1 шаг назад
alembic downgrade -1
```

## API Endpoints

### Сервисные
- `GET /` — Приветственное сообщение
- `GET /health` — Проверка состояния API
- `GET /docs` — Интерактивная документация Swagger

### Основные ресурсы
- `/auth` — Регистрация и аутентификация (JWT)
- `/users` — Управление профилями пользователей
- `/apartments` — Каталог квартир и гео-поиск (PostGIS)
- `/bookings` — Создание и управление бронированиями
- `/photos` — Загрузка изображений объектов в MinIO

## Лицензия

MIT