"""Shared test fixtures and configuration."""

import os
from collections.abc import Generator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db
from app.models import Apartment, Base, Client, Landlord, User
from app.routers import apartments, bookings, clients, landlords, payments, photos, users
from geoalchemy2.types import Geography


# Use PostgreSQL from environment variable, fallback to SQLite for local testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    test_engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    test_engine = create_engine(DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def create_test_app() -> FastAPI:
    """Create a test FastAPI application without database connection in lifespan."""

    @asynccontextmanager
    async def test_lifespan(_app: FastAPI):
        """Test lifespan that creates/drops tables."""
        Base.metadata.create_all(bind=test_engine)
        yield

    test_app = FastAPI(
        title="Posutochka API Test",
        description="API for apartment rental service",
        version="1.0.0",
        lifespan=test_lifespan,
    )

    # Include all routers
    test_app.include_router(users.router)
    test_app.include_router(landlords.router)
    test_app.include_router(clients.router)
    test_app.include_router(apartments.router)
    test_app.include_router(photos.router)
    test_app.include_router(bookings.router)
    test_app.include_router(payments.router)

    @test_app.get("/")
    def root():
        """Root endpoint."""
        return {"message": "Welcome to Posutochka API"}

    @test_app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return test_app


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after the test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    test_app = create_test_app()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    test_app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "phone_number": "+1234567890",
        "password_hash": "securepassword123",
        "telegram_username": "@testuser",
    }

@pytest.fixture
def sample_apartment_data() -> dict[str, Any]:
    """Sample apartment data for testing."""
    return {
        "name": "Cozy Studio",
        "description": "A beautiful studio apartment in the city center",
        "price_per_night": 50.0,
        "address": "123 Main Street",
        "location": "POINT (37.6173 55.7558)",  # Moscow coordinates
    }
 # "location": Point([37.6173, 55.7558])
        # "location": {"type": "Geography", "coordinates": [37.6173, 55.7558]}#,"ctx":{"class":"Geography"}  # Используйте GeoJSON


@pytest.fixture
def sample_landlord_data() -> dict[str, Any]:
    """Sample landlord data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
    }


@pytest.fixture
def sample_client_data() -> dict[str, Any]:
    """Sample client data for testing."""
    return {
        "first_name": "Jane",
        "last_name": "Smith",
    }


@pytest.fixture
def sample_booking_data() -> dict[str, Any]:
    """Sample booking data for testing."""
    return {
        "start_date": "2024-01-15T14:00:00",
        "end_date": "2024-01-20T11:00:00",
        "cost": 250.0,
        "booking_status": "pending",
    }


@pytest.fixture
def sample_payment_data() -> dict[str, Any]:
    """Sample payment data for testing."""
    return {
        "amount": 250.0,
        "payment_status": "pending",
    }


@pytest.fixture
def sample_photo_data() -> dict[str, Any]:
    """Sample photo data for testing."""
    return {
        "url": "https://example.com/photos/apartment1.jpg",
    }


@pytest.fixture
def created_user(db_session: Session, sample_user_data: dict[str, Any]) -> User:
    """Create and return a user in the database."""
    user = User(
        email=sample_user_data["email"],
        phone_number=sample_user_data["phone_number"],
        password_hash=sample_user_data["password_hash"],
        telegram_username=sample_user_data["telegram_username"],
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def created_apartment(db_session: Session, sample_apartment_data: dict[str, Any]) -> Apartment:
    """Create and return an apartment in the database."""
    apartment = Apartment(
        name=sample_apartment_data["name"],
        description=sample_apartment_data["description"],
        price_per_night=sample_apartment_data["price_per_night"],
        address=sample_apartment_data["address"],
        location=sample_apartment_data["location"],
    )
    db_session.add(apartment)
    db_session.commit()
    db_session.refresh(apartment)
    return apartment


@pytest.fixture
def created_landlord(
    db_session: Session, created_user: User, sample_landlord_data: dict[str, Any]
) -> Landlord:
    """Create and return a landlord in the database."""
    landlord = Landlord(
        user_id=created_user.id,
        first_name=sample_landlord_data["first_name"],
        last_name=sample_landlord_data["last_name"],
    )
    db_session.add(landlord)
    db_session.commit()
    db_session.refresh(landlord)
    return landlord


@pytest.fixture
def created_client_user(db_session: Session) -> User:
    """Create and return a client user in the database."""
    user = User(
        email="client@example.com",
        phone_number="+0987654321",
        password_hash="clientpassword123",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def created_client(
    db_session: Session, created_client_user: User, sample_client_data: dict[str, Any]
) -> Client:
    """Create and return a client in the database."""
    client_obj = Client(
        user_id=created_client_user.id,
        first_name=sample_client_data["first_name"],
        last_name=sample_client_data["last_name"],
    )
    db_session.add(client_obj)
    db_session.commit()
    db_session.refresh(client_obj)
    return client_obj
