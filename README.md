### Пример структуры базы данных

```sql
CREATE TABLE User (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(15) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK(role IN ('landlord', 'client', 'moderator')),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Landlord (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES User(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL
);

CREATE TABLE Client (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES User(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL
);

CREATE TABLE Moderator (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES User(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL
);

CREATE TABLE Apartment (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_per_night DECIMAL(10, 2) NOT NULL,
    location VARCHAR(255) NOT NULL,
    photos_ids INTEGER[] -- массив IDs фотографий
);

CREATE TABLE Photo (
    id SERIAL PRIMARY KEY,
    apartment_id INTEGER REFERENCES Apartment(id),
    url VARCHAR(255) NOT NULL
);

CREATE TABLE Booking (
    id SERIAL PRIMARY KEY,
    landlord_id INTEGER REFERENCES Landlord(user_id),
    client_id INTEGER REFERENCES Client(user_id),
    apartment_id INTEGER REFERENCES Apartment(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    booking_status VARCHAR(50) NOT NULL CHECK(booking_status IN ('pending', 'confirmed', 'cancelled'))
);

CREATE TABLE Payment (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES Booking(id),
    amount DECIMAL(10, 2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_status VARCHAR(50) NOT NULL CHECK(payment_status IN ('paid', 'pending', 'failed'))
);
____________________________________
### Обновленные сущности

#### Пользователь (User)
- **Описание**: Основная сущность для всех типов пользователей.
- **Поля**:
  - `id` (уникальный, первичный ключ)
  - `email`
  - `phone_number`
  - `password_hash`
  - `role` (enum: "арендодатель", "клиент", "модератор")
  - `registration_date`
  - `telegram_username` (опциональное поле для Telegram-идентификатора)

#### Арендодатель (Landlord)
- **Описание**: Подкласс пользователя, который предоставляет апартаменты в аренду.
- **Поля**:
  - `id` (уникальный, первичный ключ)
  - `user_id` (ссылается на ID пользователя в таблице User)
  - `first_name`
  - `last_name`

#### Клиент (Client)
- **Описание**: Подкласс пользователя, который арендует апартаменты.
- **Поля**:
  - `id` (уникальный, первичный ключ)
  - `user_id` (ссылается на ID пользователя в таблице User)
  - `first_name`
  - `last_name`

#### Модератор (Moderator)
- **Описание**: Подкласс пользователя, ответственный за управление контентом и бронированиями.
- **Поля**:
  - `id` (уникальный, первичный ключ)
  - `user_id` (ссылается на ID пользователя в таблице User)
  - `first_name`
  - `last_name`

#### Апартамент (Apartment)
- **Описание**: Сущность для описания арендуемых объектов.
- **Поля**:
  - `id` (уникальный, первичный ключ)
  - `name`
  - `description`
  - `price_per_night`
  - `location`
  - `photos_ids` (массив для хранения IDs фотографий)

#### Фото (Photo)
- **Описание**: Сущность для хранения фотографий апартаментов.
- **Поля**:
  - `id` (уникальный, первичный ключ)
  - `apartment_id` (ссылается на ID апартамента в таблице Apartment)
  - `url`

#### Бронирование (Booking)
- **Описание**: Сущность для хранения информации о бронированиях.
- **Поля**:
  - `id` (уникальный, первичный ключ)
  - `landlord_id` (ссылается на ID арендодателя в таблице Landlord)
  - `client_id` (ссылается на ID клиента в таблице Client)
  - `apartment_id` (ссылается на ID апартамента в таблице Apartment)
  - `start_date`
  - `end_date`
  - `cost`
  - `booking_status`

#### Оплата (Payment)
- **Описание**: Сущность для хранения информации об оплатах.
- **Поля**:
  - `id` (уникальный, первичный ключ)
  - `booking_id` (ссылается на ID бронирования в таблице Booking)
  - `amount`
  - `payment_date`
  - `payment_status`


### Интеграция с FastAPI

aiogram
`aiogram` — это мощная библиотека для создания Telegram-ботов на Python, которая использует асинхронное программирование с помощью `asyncio`. Она позволяет разработчикам создавать 
сложные и быстрые боты, которые могут обрабатывать множество запросов одновременно.

### Основные особенности `aiogram`:

1. **Асинхронность**: Использует асинхронное программирование с помощью `async/await`, что позволяет эффективно обрабатывать несколько запросов одновременно.
2. **Легкость использования**: Простой и интуитивный API, который упрощает создание ботов.
3. **Поддержка всех возможностей Telegram API**: Полная поддержка всех функций Telegram API.
4. **Кастомизация**: Позволяет легко настраивать обработчики сообщений и команд.

### Установка

Чтобы начать использовать `aiogram`, сначала установите его с помощью pip:

```bash
pip install aiogram
```

### Базовый пример бота

Давайте создадим простого бота, который будет приветствовать пользователей.

```python
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
import logging

# Установка логирования
logging.basicConfig(level=logging.INFO)

# Ваш токен бота
API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я твой Telegram-бот.")

# Запуск бота
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
```

### Обработка сообщений и команд

В `aiogram` обработчики создаются с помощью декораторов. Вот пример более сложного бота, который отвечает на текстовые сообщения:

```python
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import CommandStart, Text
import logging

API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я твой Telegram-бот. Напиши 'помощь', чтобы узнать, что я могу.")

@dp.message_handler(Text(equals='помощь'))
async def send_help(message: types.Message):
    help_text = (
        "Я могу:\n"
        "- Отвечать на приветствия.\n"
        "- Рассказывать шутки (если ты напишешь 'шутка').\n"
    )
    await message.reply(help_text)

@dp.message_handler(Text(equals='шутка'))
async def tell_joke(message: types.Message):
    joke = "Почему программисты не едят еду в буфете? Потому что она 'буферизирована'!"
    await message.reply(joke)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
```

### Подключение к базе данных

`aiogram` не имеет встроенной поддержки для работы с базами данных, но вы можете использовать любую библиотеку для взаимодействия с базой данных. Например, `asyncpg` или `aiosqlite` 
для PostgreSQL и SQLite соответственно.

Вот пример использования `asyncpg`:

```python
import asyncpg

# Функция для подключения к базе данных
async def create_pool():
    pool = await asyncpg.create_pool(user='user', password='password', database='database', host='localhost')
    return pool

@dp.message_handler(commands=['add_user'])
async def add_user(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Подключение к базе данных
    pool = await create_pool()
    
    async with pool.acquire() as connection:
        await connection.execute("INSERT INTO users (user_id, username) VALUES ($1, $2)", user_id, username)
    
    await message.reply("Пользователь добавлен в базу данных.")
```

### Заключение

`aiogram` — это мощный инструмент для создания Telegram-ботов на Python. С его помощью можно создавать сложные и функциональные боты, используя современные возможности асинхронного 
программирования. Не забывайте про документацию `aiogram`, которая содержит много полезной информации и примеров использования.
___________________________________
### 3. Встраивание карты OpenStreetMap с использованием iframe

Вы можете встроить карту OpenStreetMap непосредственно в сообщение бота с помощью HTML и iframe.

```python
from aiogram import Bot, Dispatcher, types
import logging

API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['osm_iframe'])
async def show_osm_map_iframe(message: types.Message):
    iframe_url = "https://www.openstreetmap.org/export/embed.html?bbox=37.59401699829101%2C55.75277306079635%2C37.62001658630371%2C55.7618361743281&layer=mapnik"
    await message.reply(
        f"<a href='{iframe_url}'>Показать карту</a>",
        parse_mode=types.ParseMode.HTML
    )

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
```
______________________________________


### Шаг 1: Создание проекта FastAPI

Сначала установите необходимые библиотеки:

```bash
pip install fastapi uvicorn leaflet python-dotenv
```

### Шаг 2: Создайте файл `main.py` для вашего приложения FastAPI

В этом файле мы создадим API, который принимает список координат и возвращает HTML-страницу с картой:

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import requests
from jinja2 import Environment, select_autoescape
import os

app = FastAPI()

# Загрузка шаблона HTML из файла
template_env = Environment(
    autoescape=select_autoescape(['html', 'xml']),
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
)

@app.get("/apartment_map", response_class=HTMLResponse)
async def apartment_map(request: Request, coords_str: str):
    try:
        # Разбор JSON-строки в список координат
        coords = json.loads(coords_str)
        
        if not isinstance(coords, list) or not all(isinstance(coord, list) and len(coord) == 2 for coord in coords):
            raise ValueError("Invalid coordinates format")

        template = template_env.get_template('map.html')
        return template.render(coords=coords)

    except Exception as e:
        return HTMLResponse(content=str(e), status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Шаг 3: Создайте файл `templates/map.html` для шаблона HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Apartment Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
</head>
<body>
    <div id="map"></div>
    <script>
        function initMap(coords) {
            var map = L.map('map').setView([55.75, 37.62], 12);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            var markerCluster = L.markerClusterGroup();

            coords.forEach(coord => {
                var marker = L.marker(coord).bindPopup('Apartment');
                markerCluster.addLayer(marker);
            });

            map.addLayer(markerCluster);
        }

        window.onload = function() {
            initMap({{ json.dumps(coords) }});
        };
    </script>
</body>
</html>
```

### Шаг 4: Запуск приложения

Запустите ваше FastAPI-приложение:

```bash
uvicorn main:app --reload
```

### Дополнительные оптимизации и улучшения:

1. **Кэширование**: Рассмотрите возможность кэширования HTML-страницы с картой, чтобы избежать повторной генерации для одинаковых запросов.
   
2. **Оптимизация данных**: Если координат много, подумайте о том, как можно их фильтровать или уменьшить количество передаваемых на клиент.

3. **Обработка ошибок**: Добавьте более подробные сообщения об ошибках и логирование для отладки.

### Пример использования

Вы можете отправить GET-запрос на `/apartment_map` с параметром `coords`, например:

```bash
curl "http://127.0.0.1:8000/apartment_map?coords=[[-33.86, 151.209],[-27.44, 153.029]]"
```

Это вернет HTML-страницу с картой, отображающей указанные координаты.

### Примечание

Для более сложных сценариев можно рассмотреть использование асинхронного HTTP клиента, такого как `httpx`, чтобы загружать данные с сервера без блокировки основного цикла событий 
FastAPI.

____________________________________________

отношения Пользователя к Клиенту и Арендодателю один ко одному


### Один ко Одному

Вот как вы можете определить отношение "один к одному" между моделями `User` и `Client`, используя SQLAlchemy:

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    client_id = Column(Integer, ForeignKey('client.id'), nullable=True)
    client = relationship("Client", back_populates="user", uselist=False)

class Client(Base):
    __tablename__ = 'client'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'))
    name = Column(String, nullable=False)

    user = relationship("User", back_populates="client", uselist=False)
```

### Объяснение:

1. **Внешний ключ в `Client`**:
   - В модели `Client`, поле `user_id` является внешним ключом, ссылающимся на таблицу `user`.
   - Установлено `ondelete='CASCADE'`, чтобы при удалении пользователя автоматически удалялся и связанный клиент.

2. **Внешний ключ в `User`**:
   - В модели `User`, поле `client_id` является внешним ключом, ссылающимся на таблицу `client`.
   - Установлено `nullable=True`, чтобы пользователь мог существовать без клиента.
   - Используется отношение `uselist=False`, так как ожидается только один клиент на пользователя.

3. **Отношения**:
   - В обеих моделях используется `relationship` с параметром `back_populates`, чтобы установить двустороннюю связь между `User` и `Client`.

### Ограничение "один ко одному"

Чтобы гарантировать, что у каждого пользователя есть только один клиент (и наоборот), вы можете использовать ограничения целостности данных. В SQLAlchemy это можно сделать с помощью 
метода `UniqueConstraint`:

```python
from sqlalchemy import UniqueConstraint

class User(Base):
    # ...
    
    __table_args__ = (
        UniqueConstraint('client_id', name='unique_client_per_user'),
    )

class Client(Base):
    # ...

    __table_args__ = (
        UniqueConstraint('user_id', name='unique_user_per_client'),
    )
```

Эти ограничения гарантируют, что в базе данных не будет нарушено правило "один ко одному".
