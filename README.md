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

Что делать дальше?
Теперь, когда фундамент готов, можно переходить к «бизнес-логике». Выбирайте приоритет:

    Уведомление клиента: Сделать так, чтобы когда вы пишете «Подтверждаю» в боте, этот текст не только сохранялся в базу, но и отправлялся клиенту (например, в другой чат или через API).
    Система статусов: Настроить автоматическую смену статуса бронирования. Если арендодатель ответил «ОК», менять статус с pending на confirmed.
    Кнопки (Inline Keyboard): Добавить арендодателю кнопки прямо в Telegram: [✅ Подтвердить] и [❌ Отказать], чтобы ему не нужно было писать текст вручную.

Какую фичу внедряем следующей?

https://api.telegram.org/bot8508648552:AAGhEs_7LhZT7qFyPZCk39gONvOpZ1dcRL0/getWebhookInfo
https://api.telegram.org/botмойтокен/setWebhook?url=https://legal-breads-grow.loca.lt/chat/
https://api.telegram.org/bot8508648552:AAGhEs_7LhZT7qFyPZCk39gONvOpZ1dcRL0/deleteWebhook?drop_pending_updates=true

Пинги
___________________________________
ssh -p 443 -R0:localhost:8000 a.pinggy.io
ssh -p 443 -R0:localhost:8000 a.pinggy.io
The authenticity of host '[a.pinggy.io]:443 ([172.233.242.88]:443)' can't be established.
RSA key fingerprint is SHA256:nFd5rfJMGuZXvfeRzJ/BtT3TfksAxTWMajcrHRcI7AM.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? 
 Your tunnel will expire in 60 minutes. Upgrade to Pinggy Pro to get unrestricted tunnels. https://dashboard.pinggy.io


   http://saojz-95-24-30-141.a.free.pinggy.link
   https://saojz-95-24-30-141.a.free.pinggy.link
   https://api.telegram.org/bot8508648552:AAGhEs_7LhZT7qFyPZCk39gONvOpZ1dcRL0/setWebhook?url=https://saojz-95-24-30-141.a.free.pinggy.link
    
    https://api.telegram.org/bot8508648552:AAGhEs_7LhZT7qFyPZCk39gONvOpZ1dcRL0/getWebhookInfo

docker run -d --name redis-posutochka -p 6379:6379 redis:7-alpine
docker pull redis:7-alpine
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

Что можно сделать дальше:

    - Роли и права: У тебя в модели User уже заложены поля landlord, client, investor. Теперь можно добавить проверку прав (например, только landlord может загружать фото квартир).
    - Валидация документов: Можно добавить автоматическую проверку типа файла (magic numbers), чтобы под видом .pdf не загрузили исполняемый файл.
    - Добавить автоматическое сжатие фото при загрузке.
    - Реализовать отправку уведомлений через бота при регистрации или новом бронировании.
    
    - сейчас любой авторизованный пользователь может вызвать любой эндпоинт.

    Что сделать: Написать зависимости (Depends), которые проверяют, является ли current_user арендодателем.
    Зачем: Чтобы обычный клиент не смог случайно (или специально) удалить чужую квартиру или загрузить фото в чужой объект.



    docker exec -it posutochka_storage mc alias set myminio http://localhost:9000 admin strong_password_2026
    docker exec -it posutochka_storage mc anonymous set download myminio/apartments


http://localhost:9001/browser/apartments
Что это значит для твоего проекта «Посуточка 2026»:

    Фронтенд (Next.js): Теперь в базе данных в таблице photos должны лежать именно такие ссылки: http://localhost:9000/apartments/имя_файла.jpg.
    Бэкенд (FastAPI): Твой роутер для загрузки фото теперь будет работать «как часы». Он примет файл, сохранит его в бакет apartments и отдаст фронту готовую рабочую ссылку.
    Docker: Вся связка (PostGIS + Redis + MinIO + Celery) полностью готова к реальной работе.
docker logs posutochka_app
docker exec -it posutochka_postgres psql -U postgres -d posutochka -c "CREATE EXTENSION IF NOT EXISTS btree_gist; CREATE EXTENSION IF NOT EXISTS postgis;"

docker compose down -v  # Удалит контейнеры и ОЧИСТИТ старую базу (обязательно!)
docker compose up -d    # Запустит всё с нуля, выполнит init.sql, а затем код приложения
docker compose exec app python scripts/seed_apartm.py
docker compose logs -f app -ошибки в контейнерах в реальном времени
docker compose logs pinggy
python3 -c "from app.main import app; print([r.path for r in app.routes])" смотрим пути проекта

find . -name "__pycache__" -exec rm -rf {} +
 uvicorn app.main:app --reload
 
 https://velocity-issues-palm-sampling.trycloudflare.com
 https://api.telegram.org/bot8508648552:AAGhEs_7LhZT7qFyPZCk39gONvOpZ1dcRL0/setWebhook?url=https://velocity-issues-palm-sampling.trycloudflare.com
 ________________________
___________________
Что можно сделать следующим шагом:

    Загрузка реальных фото: Реализовать в FastAPI эндпоинт, который принимает файл и отправляет его в ваш бакет apartments в MinIO.
    Гео-поиск: Использовать возможности PostGIS, чтобы пользователь мог искать квартиры, просто двигая карту (передавая координаты границ экрана — BBox).
    Telegram-уведомления: Раз у вас в конфиге уже есть worker и beat, можно настроить бота, который будет присылать арендодателю уведомление о новом бронировании.
    
INSERT INTO apartment (name, address, price_per_night, description, location, landlord_id) VALUES
('Студия у Эрмитажа', 'Миллионная ул., 5', 5500, 'Центр города, вид на Неву.', ST_SetSRID(ST_MakePoint(30.3158, 59.9436), 4326), 1),
('Лофт на Петроградке', 'Большой пр. ПС, 44', 4200, 'Стильный интерьер, высокие потолки.', ST_SetSRID(ST_MakePoint(30.3015, 59.9590), 4326), 1),
('Уют на Ваське', '6-я линия В.О., 12', 3800, 'Тихий двор, рядом метро.', ST_SetSRID(ST_MakePoint(30.2785, 59.9400), 4326), 1),
('Пентхаус на Лиговке', 'Лиговский пр., 50', 8500, 'Панорамные окна, терраса.', ST_SetSRID(ST_MakePoint(30.3555, 59.9248), 4326), 1),
('Квартира у Новой Голландии', 'наб. Адмиралтейского канала, 15', 4800, 'Рядом с парком.', ST_SetSRID(ST_MakePoint(30.2890, 59.9295), 4326), 1);
 смена порта в базе в контейнере 1. замена 5433:5432 в ямль и 2. docker-compose up -d --force-recreate db
 ___________________________________________________
 удаляем если запутались.
 docker exec -it posutochka_postgres psql -U postgres -d posutochka -c "DROP TABLE IF EXISTS alembic_version;"
 docker exec -it posutochka_postgres psql -U postgres -d posutochka -c "DROP TABLE IF EXISTS \"user\" CASCADE; DROP TABLE IF EXISTS alembic_version;"

# Удаляем ВСЕ таблицы, чтобы Alembic создал их по моделям с нуля
docker exec -it posutochka_postgres psql -U postgres -d posutochka -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"
# Теперь нужно заново создать расширения (так как схема public была пересоздана)
docker exec -it posutochka_postgres psql -U postgres -d posutochka -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS btree_gist;"
docker exec -it posutochka_app alembic revision --autogenerate -m "initial_schema"
docker exec -it posutochka_app alembic upgrade head
docker compose down -v
docker exec -it containerpostgres psql -U postgres -d posutochka -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS btree_gist;"
docker run -d \
  --name containerpostgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=123456 \
  -e POSTGRES_DB=posutochka \
  -p 5434:5432 \
  postgis/postgis:16-3.4

docker system prune
docker volume prune
docker rm $(docker ps -a -q)
docker stop $(docker ps -q)
если не сохранияется 
sudo chown -R $USER:$USER .

docker run -d \
  --name posutochka_redis_test \
  -p 6380:6379 \
  redis:7-alpine

  docker exec -it posutochka_app alembic revision --autogenerate -m "add_booking_constraints"
docker exec -it posutochka_app alembic upgrade head
_________________________
 user_data = sample_user_data_factory()
    
    # 1. Извлекаем чистый пароль для логина
    raw_password = user_data.pop("password") 
    
    # 2. Убираем password_hash, если хотим захешировать его правильно через сервис
    user_data.pop("password_hash", None)
    
    # 3. Теперь в user_data нет лишних ключей, и SQLAlchemy не ругается
    user = User(**user_data)
    user.password_hash = AuthService.get_password_hash(raw_password)
    
    db_session.add(user)
    await db_session.commit()
    ______________________________
    tests/test_booking_tasks.py
    tests/test_bookings.py