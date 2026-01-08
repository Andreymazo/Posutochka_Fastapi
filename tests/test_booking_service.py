"""Tests for booking service business logic."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.apartment import Apartment
from app.models.apartmentavailability import ApartmentAvailability
from app.models.base import Base
from app.models.booking import Booking
from app.models.client import Client
from app.models.landlord import Landlord
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingStatus
from app.services.booking_service import BookingService


# Async test database setup
@pytest.fixture
async def async_db_session():
    """Create an async database session for testing."""
    # Use in-memory SQLite for fast async tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def sample_user(async_db_session: AsyncSession):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        phone_number="+1234567890",
        password_hash="hashedpassword",
        telegram_username="@testuser",
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest.fixture
async def sample_landlord(async_db_session: AsyncSession, sample_user: User):
    """Create a sample landlord for testing."""
    landlord = Landlord(
        user_id=sample_user.id,
        first_name="John",
        last_name="Doe",
    )
    async_db_session.add(landlord)
    await async_db_session.commit()
    await async_db_session.refresh(landlord)
    return landlord


@pytest.fixture
async def sample_client_user(async_db_session: AsyncSession):
    """Create a sample client user for testing."""
    user = User(
        email="client@example.com",
        phone_number="+0987654321",
        password_hash="hashedpassword",
        telegram_username="@clientuser",
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest.fixture
async def sample_client(async_db_session: AsyncSession, sample_client_user: User):
    """Create a sample client for testing."""
    client = Client(
        user_id=sample_client_user.id,
        first_name="Jane",
        last_name="Smith",
    )
    async_db_session.add(client)
    await async_db_session.commit()
    await async_db_session.refresh(client)
    return client


@pytest.fixture
async def sample_apartment(async_db_session: AsyncSession, sample_landlord: Landlord):
    """Create a sample apartment for testing."""
    apartment = Apartment(
        name="Test Apartment",
        description="A nice apartment",
        price_per_night=100.0,
        address="123 Test St",
        location="POINT(37.6173 55.7558)",
        landlord_id=sample_landlord.id,
    )
    async_db_session.add(apartment)
    await async_db_session.commit()
    await async_db_session.refresh(apartment)
    return apartment


@pytest.mark.asyncio
class TestBookingService:
    """Test suite for BookingService."""

    async def test_create_booking_success(
        self,
        async_db_session: AsyncSession,
        sample_landlord: Landlord,
        sample_client: Client,
        sample_apartment: Apartment,
    ):
        """Test successfully creating a booking when dates are available."""
        booking_data = BookingCreate(
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 5),
            cost=400.0,
            booking_status=BookingStatus.pending,
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )

        booking = await BookingService.create_new_booking(
            db=async_db_session, booking_data=booking_data, client_id=sample_client.id
        )

        assert booking.id is not None
        assert booking.booking_period.lower == date(2024, 6, 1)
        assert booking.booking_period.upper == date(2024, 6, 5)
        assert booking.cost == Decimal("400.0")
        assert booking.booking_status == "pending"

    async def test_create_booking_blocked_period(
        self,
        async_db_session: AsyncSession,
        sample_landlord: Landlord,
        sample_client: Client,
        sample_apartment: Apartment,
    ):
        """Test that booking fails when dates are blocked by landlord."""
        # Create a blocked period
        blocked_period = ApartmentAvailability(
            apartment_id=sample_apartment.id,
            blocked_period=Range(date(2024, 7, 1), date(2024, 7, 10), bounds="[)"),
            reason="Ремонт",
            is_blocked=True,
        )
        async_db_session.add(blocked_period)
        await async_db_session.commit()

        # Try to create a booking that overlaps with blocked period
        booking_data = BookingCreate(
            start_date=date(2024, 7, 5),
            end_date=date(2024, 7, 8),
            cost=300.0,
            booking_status=BookingStatus.pending,
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await BookingService.create_new_booking(
                db=async_db_session, booking_data=booking_data, client_id=sample_client.id
            )

        assert exc_info.value.status_code == 400
        assert "заняты или недоступны" in exc_info.value.detail

    async def test_create_booking_overlapping_booking(
        self,
        async_db_session: AsyncSession,
        sample_landlord: Landlord,
        sample_client: Client,
        sample_apartment: Apartment,
    ):
        """Test that booking fails when dates overlap with existing booking."""
        # Create an existing booking
        existing_booking = Booking(
            booking_period=Range(date(2024, 8, 1), date(2024, 8, 10), bounds="[)"),
            cost=900.0,
            booking_status="confirmed",
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )
        async_db_session.add(existing_booking)
        await async_db_session.commit()

        # Try to create a booking that overlaps
        booking_data = BookingCreate(
            start_date=date(2024, 8, 5),
            end_date=date(2024, 8, 12),
            cost=700.0,
            booking_status=BookingStatus.pending,
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await BookingService.create_new_booking(
                db=async_db_session, booking_data=booking_data, client_id=sample_client.id
            )

        assert exc_info.value.status_code == 400
        assert "заняты или недоступны" in exc_info.value.detail

    async def test_create_booking_cancelled_booking_allowed(
        self,
        async_db_session: AsyncSession,
        sample_landlord: Landlord,
        sample_client: Client,
        sample_apartment: Apartment,
    ):
        """Test that booking succeeds when overlapping booking is cancelled."""
        # Create a cancelled booking
        cancelled_booking = Booking(
            booking_period=Range(date(2024, 9, 1), date(2024, 9, 10), bounds="[)"),
            cost=900.0,
            booking_status="cancelled",
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )
        async_db_session.add(cancelled_booking)
        await async_db_session.commit()

        # Create a new booking that overlaps with cancelled one
        booking_data = BookingCreate(
            start_date=date(2024, 9, 5),
            end_date=date(2024, 9, 12),
            cost=700.0,
            booking_status=BookingStatus.pending,
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )

        booking = await BookingService.create_new_booking(
            db=async_db_session, booking_data=booking_data, client_id=sample_client.id
        )

        assert booking.id is not None
        assert booking.booking_status == "pending"

    async def test_create_booking_min_stay_requirement(
        self,
        async_db_session: AsyncSession,
        sample_landlord: Landlord,
        sample_client: Client,
        sample_apartment: Apartment,
    ):
        """Test that booking fails when minimum stay requirement is not met."""
        # Create an availability rule with minimum stay of 3 days
        availability_rule = ApartmentAvailability(
            apartment_id=sample_apartment.id,
            blocked_period=Range(date(2024, 10, 1), date(2024, 10, 31), bounds="[)"),
            reason="Праздничные дни",
            is_blocked=False,
            min_stay_days=3,
        )
        async_db_session.add(availability_rule)
        await async_db_session.commit()

        # Try to create a booking with only 2 days
        booking_data = BookingCreate(
            start_date=date(2024, 10, 5),
            end_date=date(2024, 10, 7),  # 2 days
            cost=200.0,
            booking_status=BookingStatus.pending,
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )

        with pytest.raises(HTTPException) as exc_info:
            await BookingService.create_new_booking(
                db=async_db_session, booking_data=booking_data, client_id=sample_client.id
            )

        assert exc_info.value.status_code == 400
        assert "Минимальный срок проживания" in exc_info.value.detail
        assert "3 дней" in exc_info.value.detail

    async def test_get_booking_by_id(
        self,
        async_db_session: AsyncSession,
        sample_landlord: Landlord,
        sample_client: Client,
        sample_apartment: Apartment,
    ):
        """Test retrieving a booking by ID."""
        # Create a booking
        booking = Booking(
            booking_period=Range(date(2024, 11, 1), date(2024, 11, 5), bounds="[)"),
            cost=400.0,
            booking_status="pending",
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )
        async_db_session.add(booking)
        await async_db_session.commit()
        await async_db_session.refresh(booking)

        # Retrieve it
        retrieved = await BookingService.get_booking_by_id(
            db=async_db_session, booking_id=booking.id
        )

        assert retrieved.id == booking.id
        assert retrieved.cost == Decimal("400.0")

    async def test_get_booking_not_found(self, async_db_session: AsyncSession):
        """Test that getting non-existent booking raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            await BookingService.get_booking_by_id(db=async_db_session, booking_id=99999)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    async def test_get_bookings_with_filters(
        self,
        async_db_session: AsyncSession,
        sample_landlord: Landlord,
        sample_client: Client,
        sample_apartment: Apartment,
    ):
        """Test retrieving bookings with filters."""
        # Create multiple bookings
        booking1 = Booking(
            booking_period=Range(date(2024, 12, 1), date(2024, 12, 5), bounds="[)"),
            cost=400.0,
            booking_status="pending",
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )
        booking2 = Booking(
            booking_period=Range(date(2025, 1, 1), date(2025, 1, 5), bounds="[)"),
            cost=500.0,
            booking_status="confirmed",
            landlord_id=sample_landlord.id,
            client_id=sample_client.id,
            apartment_id=sample_apartment.id,
        )
        async_db_session.add_all([booking1, booking2])
        await async_db_session.commit()

        # Get bookings for this apartment
        bookings = await BookingService.get_bookings(
            db=async_db_session, apartment_id=sample_apartment.id
        )

        assert len(bookings) == 2
        assert all(b.apartment_id == sample_apartment.id for b in bookings)
