# Posutochka API & Frontend

Сервис краткосрочной аренды квартир (аналог AirBnB/Суточно.ру). Проект включает бэкенд на **FastAPI**, фронтенд на **Next.js**, фоновые задачи через **Celery** и хранилище картинок **MinIO**.

---

## 🏗️ Как устроена архитектура проекта

В проекте используется **гибридная схема запуска**:
1. **Инфраструктура ядра (База и Кэш)** — запускаются как независимые глобальные Docker-контейнеры. Это защищает данные от случайного удаления при перезапуске приложения.
2. **Приложение и Сервисы** — (`FastAPI`, `Next.js`, `Celery Worker/Beat`, `MinIO`) запускаются вместе через единый `docker-compose.yml` и общаются с ядром через системный шлюз `host.docker.internal`.

---

## 🚀 Быстрый старт

### Шаг 1: Запуск базовой инфраструктуры (Ядро)

Перед запуском основного приложения необходимо поднять базу данных и брокер очередей. Запустите в терминале следующие команды:

```bash
# 1. Запуск PostgreSQL 16 с поддержкой гео-данных (PostGIS) на порту 5434
docker run -d \
  --name containerpostgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=123456 \
  -e POSTGRES_DB=posutochka \
  -p 5434:5432 \
  postgis/postgis:16-3.4

# 2. Активация необходимых расширений PostGIS внутри базы данных
docker exec -it containerpostgres psql -U postgres -d posutochka -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS btree_gist;"

# 3. Запуск Redis 7 для Celery и кэша на порту 6380
docker run -d \
  --name posutochka_redis_test \
  -p 6380:6379 \
  redis:7-alpine
```

### Шаг 2: Настройка окружения

Создайте файл `.env` в корневой директории проекта:
```bash
cp .env.example .env
```
*Убедитесь, что внутри `.env` указан ваш актуальный токен `TELEGRAM_BOT_TOKEN` для работы уведомлений.*

### Шаг 3: Запуск приложения и фронтенда

Теперь запускаем всю экосистему проекта одной командой:
```bash
# Сборка и запуск контейнеров приложения
docker compose up -d --build

# Применение миграций базы данных (создание таблиц)
docker compose exec app alembic upgrade head

# (Опционально) Наполнение базы тестовыми квартирами в Санкт-Петербурге
docker compose exec app python scripts/seed_apartm.py
```

**После этого проект полностью готов к работе:**
* 🌍 **Фронтенд (Next.js):** [http://localhost:3000](http://localhost:3000)
* ⚙️ **Бэкенд API (FastAPI):** [http://localhost:8000](http://localhost:8000)
* 📄 **Документация Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
* 🗄️ **Панель MinIO (Хранилище фото):** [http://localhost:9001](http://localhost:9001) (Логин: `admin` / Пароль: `strong_password_2026`)

---

## 🛠️ Разработка и полезные команды

### Работа с миграциями (Alembic)
Если вы изменили модели данных в коде, выполните:
```bash
# Создать файл миграции автоматически
docker compose exec app alembic revision --autogenerate -m "описание_изменений"

# Применить изменения к базе данных
docker compose exec app alembic upgrade head

# Откатить последнюю миграцию на один шаг назад
docker compose exec app alembic downgrade -1
```

### Тестирование и линтинг
Команды выполняются внутри контейнера приложения:
```bash
# Запуск автотестов с коротким выводом ошибок
docker compose exec app pytest tests/ -v --tb=short

# Проверка кода линтером Ruff
docker compose exec app ruff check .

# Автоматическое форматирование кода по стандартам Pep8
docker compose exec app ruff format .
```

### Просмотр логов в реальном времени
```bash
docker compose logs -f app       # Логи FastAPI бэкенда
docker compose logs -f worker    # Логи фонового воркера Celery
```

---

## 📂 Структура проекта

```text
posutochka/
├── app/                        # Бэкенд приложение (FastAPI)
│   ├── main.py                 # Точка входа в API
│   ├── database.py             # Подключение к БД SQLAlchemy
│   ├── models/                 # SQLAlchemy модели данных (User, Apartment, Booking)
│   ├── routers/                # Эндпоинты API (Маршрутизация запросов)
│   ├── schemas/                # Pydantic схемы (Валидация входящих данных)
│   └── services/               # Бизнес-логика (Авторизация, хранилище MinIO)
├── posutochka-front/           # Фронтенд приложение (Next.js)
├── alembic/                    # История миграций базы данных
├── tests/                      # Автоматические тесты (pytest)
├── scripts/                    # Скрипты автоматизации и сид ТБ (seed_apartm.py)
├── docker-compose.yml          # Манифест оркестрации контейнеров приложения
└── pyproject.toml              # Конфигурация Ruff, Pytest и инструментов разработки
```

## 📜 Лицензия
MIT
