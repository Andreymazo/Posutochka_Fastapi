import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import date
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_async_db
from app.main import app

# Важно: импортируем модели, чтобы Base их "увидел"
from app.models import Apartment, Balance, Booking, Client, Landlord, User
from app.models.base import Base

# Используем psycopg3 для асинхронного PostgreSQL
DATABASE_URL = "postgresql+psycopg://postgres:123456@localhost:5433/posutochka"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncTestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
@pytest.fixture(scope="session")
def event_loop():
    """Создает экземпляр цикла событий для всей сессии тестов."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def setup_db():
    """Создание таблиц и расширений PostgreSQL один раз на всю сессию тестов."""
    async with engine.begin() as conn:
        # Необходимые расширения для ваших типов данных
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist;"))

        # Очистка и создание таблиц
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для прямого взаимодействия с БД в тестах."""
    async with AsyncTestingSessionLocal() as session:
        yield session
        # Откатываем транзакцию, чтобы изменения в БД не влияли на другие тесты
        await session.rollback()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Асинхронный клиент FastAPI с подменой сессии БД."""

    async def _override_get_async_db():
        yield db_session

    # Подменяем зависимость, которую используют роутеры
    app.dependency_overrides[get_async_db] = _override_get_async_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # Сбрасываем подмены после теста
    app.dependency_overrides.clear()



@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Генерирует уникальные данные для тестирования родительской сущности User."""
    unique_suffix = uuid.uuid4().hex[:6]
    return {
        "email": f"user_{unique_suffix}@example.com",
        "phone_number": f"+7999{uuid.uuid4().int}"[:12], # Уникальный телефон
        "password_hash": "secure_hash_2026",
        "telegram_username": f"tg_user_{unique_suffix}",
    }


@pytest.fixture
def sample_user_landlord_data() -> dict[str, Any]:
    # Генерируем случайный префикс
    uid = uuid.uuid4().hex[:6]
    return {
        "email": f"landlord_{uid}@example.com",
        "phone_number": f"+1{uuid.uuid4().int}"[:12],
        "password_hash": "landlord_pass",
        "telegram_username": f"@landlord_{uid}",
    }

@pytest.fixture
def sample_user_client_data() -> dict[str, Any]:
    uid = uuid.uuid4().hex[:6]
    return {
        "email": f"client_{uid}@example.com",
        "phone_number": f"+2{uuid.uuid4().int}"[:12],
        "password_hash": "client_pass",
        "telegram_username": f"@client_{uid}",
    }

@pytest.fixture
def sample_owner_data() -> dict[str, Any]:
    """Данные именно для сущности Owner (сумма к выплате и т.д.)."""
    return {
        "amount": 100.0,
    }

@pytest.fixture
def sample_user_owner_data() -> dict[str, Any]:
    unique_id = uuid.uuid4().hex[:6]
    return {
        "email": f"owner_{unique_id}@example.com", # Уникальный email
        "phone_number": f"+3333{unique_id}",
        "password_hash": "owner_pass",

    }


# --- CREATION FIXTURES (Асинхронное создание объектов) ---

@pytest_asyncio.fixture(loop_scope="function")
async def created_landlord_user(db_session: AsyncSession, sample_user_landlord_data: dict[str, Any]) -> User:
    """Создает пользователя специально для роли Арендодателя."""
    user = User(**sample_user_landlord_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
def sample_payment_data() -> dict[str, Any]:
    """Данные для платежа или транзакции."""
    return {
        "amount": 250.0,
        "payment_status": "pending",
        "payment_method": "card"
    }

@pytest.fixture
def sample_balance_data() -> dict[str, Any]:
    """Данные для инициализации баланса (используются в created_balance)."""
    return {
        "current_balance": 1000.0
    }

@pytest_asyncio.fixture(loop_scope="function")
async def created_balance(
    db_session: AsyncSession,
    created_landlord_user: User,
    sample_balance_data: dict[str, Any]
) -> Balance:
    """Асинхронное создание баланса в БД."""
    balance = Balance(
        user_id=created_landlord_user.id,
        current_balance=sample_balance_data["current_balance"],
    )
    db_session.add(balance)
    await db_session.commit()
    await db_session.refresh(balance)
    return balance



@pytest_asyncio.fixture(loop_scope="function")
async def created_booking(
    db_session: AsyncSession,
    created_landlord: Landlord,
    created_client: Client,
    created_apartment: Apartment,
) -> Booking:
    """Создает тестовое бронирование для использования в тестах транзакций/платежей."""
    # Используем актуальные даты 2026 года
    booking_period = Range(date(2026, 2, 1), date(2026, 2, 10), bounds="[)")

    booking = Booking(
        booking_period=booking_period,
        cost=1000.0,
        booking_status="confirmed",
        landlord_id=created_landlord.id,
        client_id=created_client.id,
        apartment_id=created_apartment.id,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)
    return booking

@pytest_asyncio.fixture(loop_scope="function")
async def created_landlord(db_session: AsyncSession, created_landlord_user: User) -> Landlord:
    """Создает Арендодателя (связан с User 1)."""
    landlord = Landlord(
        user_id=created_landlord_user.id,
        first_name="Иван",
        last_name="Хозяев"
    )
    db_session.add(landlord)
    await db_session.commit()
    await db_session.refresh(landlord)
    return landlord

@pytest_asyncio.fixture(loop_scope="function")
async def created_client_user(db_session: AsyncSession, sample_user_client_data: dict[str, Any]) -> User:
    """Создает пользователя специально для роли Клиента."""
    user = User(**sample_user_client_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(loop_scope="function")
async def created_client(db_session: AsyncSession, created_client_user: User) -> Client:
    """Создает Клиента (связан с User 2)."""
    client = Client(
        user_id=created_client_user.id,
        first_name="Петр",
        last_name="Гость"
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client

@pytest_asyncio.fixture(loop_scope="function")
async def created_owner_user(db_session: AsyncSession, sample_user_owner_data: dict[str, Any]) -> User:
    """Создает пользователя специально для роли Владельца (Owner)."""
    user = User(**sample_user_owner_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(loop_scope="function")
async def created_apartment(db_session: AsyncSession, created_landlord: Landlord) -> Apartment:
    """Создает апартаменты (требует созданного арендодателя)."""
    apartment = Apartment(
        name="Cozy Studio",
        description="A beautiful studio",
        price_per_night=50.0,
        address="123 Main Street",
        location="POINT(37.6173 55.7558)", # WKT формат для PostGIS
        landlord_id=created_landlord.id,
    )
    db_session.add(apartment)
    await db_session.commit()
    await db_session.refresh(apartment)
    return apartment

@pytest.fixture
def sample_review_data() -> dict[str, Any]:
    """Sample review data for testing."""
    return {
        "rating": 5,
        "review": "Excellent stay, highly recommended!",
    }

@pytest.fixture
async def sample_apartment_data(created_landlord: Any) -> dict[str, Any]:
    """Sample apartment data for testing (Updated for 2026)."""
    return {
        "name": "Cozy Studio",
        "description": "A beautiful studio apartment in the city center",
        "price_per_night": 50.0,
        "address": "123 Main Street",
        "location": "POINT(37.6173 55.7558)",  # Координаты Москвы
        "landlord_id": created_landlord.id,
    }
