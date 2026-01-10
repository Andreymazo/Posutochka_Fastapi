from typing import Any
from collections.abc import AsyncGenerator
import os
import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.models.base import Base  
from app.database import get_async_db
from app.main import app 
# Важно: импортируем модели, чтобы Base их "увидел"
from app.models import Apartment, Booking, Landlord, Client, User, ApartmentAvailability
import uuid

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
def sample_user_owner_data() -> dict[str, Any]:
    return {
        "email": "owner@example.com",
        "phone_number": "+3333333333",
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
# import os
# import asyncio
# import pytest
# import pytest_asyncio
# from httpx import ASGITransport, AsyncClient
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
# from sqlalchemy import text

# from app.database import Base, get_async_db
# from app.main import app  # Импортируйте ваше FastAPI приложение
# from app.models import Base # Убедитесь, что здесь подтянуты все модели

# # Схема postgresql+psycopg для асинхронной работы
# DATABASE_URL = "postgresql+psycopg://postgres:123456@localhost:5433/posutochka"

# engine = create_async_engine(DATABASE_URL, echo=False)
# AsyncTestingSessionLocal = async_sessionmaker(
#     bind=engine, 
#     class_=AsyncSession, 
#     expire_on_commit=False
# )

# @pytest_asyncio.fixture(scope="session", autouse=True)
# async def setup_db():
#     """Инициализация таблиц перед тестами."""
#     async with engine.begin() as conn:
#         # Включаем экстеншены, если их нет
#         await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
#         await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist;"))
#         # Пересоздаем таблицы для чистоты тестов
#         await conn.run_sync(Base.metadata.drop_all)
#         await conn.run_sync(Base.metadata.create_all)
#     yield
#     await engine.dispose()

# @pytest_asyncio.fixture
# async def db_session() -> AsyncSession:
#     """Сессия для создания данных в тестах."""
#     async with AsyncTestingSessionLocal() as session:
#         yield session
#         # Очищаем данные после каждого теста для изоляции
#         await session.rollback()

# @pytest_asyncio.fixture
# async def client(db_session: AsyncSession) -> AsyncClient:
#     """Асинхронный клиент с подменой зависимости БД."""
#     async def _get_test_db():
#         yield db_session

#     app.dependency_overrides[get_async_db] = _get_test_db
#     async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#         yield ac
#     app.dependency_overrides.clear()
# def create_test_app() -> FastAPI:
#     """Создает экземпляр приложения для тестов с пустым lifespan."""
    
#     @asynccontextmanager
#     async def test_lifespan(_app: FastAPI):
#         # В тестах мы управляем БД через фикстуры pytest, 
#         # поэтому здесь просто yield
#         yield

#     test_app = FastAPI(
#         title="Posutochka API Test",
#         lifespan=test_lifespan,
#     )

#     # Include all routers
#     test_app.include_router(users.router)
#     test_app.include_router(landlords.router)
#     test_app.include_router(clients.router)
#     test_app.include_router(apartments.router)
#     test_app.include_router(photos.router)
#     test_app.include_router(bookings.router)
#     test_app.include_router(payments.router)
#     test_app.include_router(balances.router)
#     test_app.include_router(reviews.router)
#     test_app.include_router(owners.router)
#     test_app.include_router(transactions.router)

#     return test_app