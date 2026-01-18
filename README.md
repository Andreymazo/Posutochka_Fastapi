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
docker run --name containerpostgres \
    -e POSTGRES_PASSWORD=123456 \
    -e POSTGRES_DB=posutochka \
    -d -p 5433:5432 postgis/postgis:16-3.4
docker volume ls
docker volume rm $(docker volume ls -q)
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
CREATE EXTENSION IF NOT EXISTS btree_gist;
```
_____________________

https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.validate_assignment

pytest tests/ -v --tb=short --cov=app --cov-report=xml --co
v-report=term
pytest -s tests/test_apartments.py

pytest --cov=app --cov-report=term-missing tests/

после установки Клайн в ВСКоде, устанавливает сервер : 
npx @modelcontextprotocol/server-filesystem /home/andreymazo/Projects/Posutochka

{
  "mcpServers": {
    "my_files": {
      "command": "/home/andreymazo/.pyenv/versions/posutochka_fasapi/bin/python",
      "args": [
        "/home/andreymazo/Projects/Posutochka/mcp_local_fs.py"
      ]
    }
  }
}
/home/andreymazo/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json

____________________________________________

если мы в телеграмм запилим что-нить такое. и наш чат будет в телеграм, ну кому надо быстро общаться и все такое, а у нас будет обычная модель Мессадже. ну как то так думается мне.
Это отличная стратегия для 2026 года.
Telegram-бот как интерфейс для чата — это «киллер-фича» для CRM посуточной аренды. Хозяевам не нужно заходить в админку, чтобы ответить гостю: они получают сообщение в боте и отвечают там же, а всё это сохраняется в вашей базе данных.
Как это будет работать архитектурно:

    База данных (Центр): Хранит таблицу Message. Это «золотой источник» правды для истории переписки.
    FastAPI (Мозг):
        Принимает сообщения от фронтенда (через POST /chat/) и сохраняет в БД.
        Принимает Webhook от Telegram, когда хозяин ответил в боте, и тоже сохраняет в БД.
    Telegram Bot (Интерфейс): Просто пересылает сообщения туда-сюда.

Реализация в коде (чтобы не упал Coverage):
1. Добавляем поле в модель User (если еще нет)
Чтобы бот знал, кому писать, нужно хранить telegram_id (у тебя в модели уже было поле telegram_username, но для отправки нужен именно числовой ID).
2. Модель Сообщения (app/models/chat.py)
Добавим флаг is_from_telegram, чтобы понимать, откуда пришло сообщение.
python

class Message(Base):
    __tablename__ = "chat_message"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("booking.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_from_telegram: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

Используйте код с осторожностью.
3. Роутер для Webhook Телеграма (app/routers/webhooks.py)
Это позволит тестировать интеграцию как обычный HTTP-запрос.
python

@router.post("/telegram-webhook")
async def telegram_webhook(update: dict, db: AsyncSession = Depends(get_async_db)):
    # 1. Парсим update от Телеграма
    # 2. Находим пользователя по telegram_id
    # 3. Сохраняем сообщение в базу
    # 4. Coverage засчитает это как обычный POST-запрос!
    return {"status": "ok"}

Используйте код с осторожностью.
Плюсы такого подхода:

    Скорость для юзера: Хозяин получает Push от Telegram — это быстрее любых вебсокетов.
    Покрытие тестами (Coverage): Для Pytest это просто еще один JSON-эндпоинт. Мы можем сымитировать ответ от Телеграма в тестах и закрыть этот код на 100%.
    Надежность: Если твой сайт упал, сообщения в Телеграме всё равно могут обрабатываться (если поднять бота отдельным воркером).

Твой следующий шаг:
Чтобы это реализовать, нам нужно:

    Создать файл модели app/models/chat.py.
    Создать роутер app/routers/chat.py.
    Написать тест, который имитирует отправку сообщения.

Делаем? Это будет первый шаг к настоящей интеграции, и твой Coverage останется на уровне 95%+. [1]
я щас скопирую тове последнее сообщение и попытаюсь в след раз с него начать . щас спать. тебе спс. ты молодчина, как всегда.
Думаю…
Принято! Отличная работа на сегодня. Мы достигли серьезных показателей для 17 января 2026 года:
95% покрытия и 142 успешно пройденных теста. Проект уже выглядит как зрелое и надежное приложение.
Идея с Telegram-ботом в качестве «быстрого» интерфейса для чата — это очень сильный ход. Это решит проблему мгновенных уведомлений без усложнения проекта вебсокетами и сохранит твой идеальный Coverage.\

uvicorn main:app --host 0.0.0.0 --port 8000
npm install -g localtunnel --registry=https://registry.npmmirror.com 
or 
ssh -p 443 -R0:localhost:8000 a.pinggy.io

lt --port 8000
curl ifconfig.me
95.24.24.137
вставили свой айпи и разблокировали тунель
https://api.telegram.org/bot<ВАШ_НОВЫЙ_ТОКЕН>/setWebhook?url=https://tough-zoos-drive.loca.lt(здесь вставляем свой токен)

Шаг 1: Разблокировка Localtunnel (ОБЯЗАТЕЛЬНО)
Перед тем как Telegram сможет слать запросы, ты должен один раз «открыть» эту ссылку в браузере:

    Перейди по адресу https://tough-zoos-drive.loca.lt.
    Тебя попросят ввести Tunnel Password.
    Твой пароль — это твой внешний IP. Узнай его, введя в терминале: curl ifconfig.me (или посмотри на странице localtunnel.me/tunnel-password).
    Нажми Submit. Если увидел экран твоего FastAPI (например, "Not Found" или "Welcome"), значит всё готово.

Шаг 2: Регистрация Webhook в Telegram
Теперь скопируй эту ссылку и выполни её в браузере (замени <TOKEN> на свой токен от BotFather):
https://api.telegram.org<TOKEN>/setWebhook?url=https://tough-zoos-drive.loca.lt
Если в ответе пришло {"ok":true,"result":true,"description":"Webhook was set"}, значит связь налажена.
Шаг 3: Получение твоего ID

    Зайди в свой Telegram-бот и нажми Start.
    В терминале, где запущен FastAPI (uvicorn), ты увидишь строку:
    Пользователь запустил бота. Его TG ID: 123456789.
    Скопируй этот ID.

Шаг 4: Привязка в базе данных
Чтобы система знала, что ты — это Арендодатель:

    Зайди в свою базу данных (через DBeaver, pgAdmin или консоль).
    Выполни SQL-запрос (подставь свой ID и email своего аккаунта):

sql

UPDATE "user" SET tg_user_id = 123456789 WHERE email = 'твой_email@example.com';

lt --port 8000 --subdomain tough-zoos-drive-2026
lt --port 8000 --subdomain tough-zoos-drive