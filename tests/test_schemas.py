"""Tests for Pydantic schemas validation."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from shapely.geometry import Point

from app.schemas.apartment import ApartmentCreate, ApartmentUpdate
from app.schemas.balance import BalanceCreate, BalanceUpdate
from app.schemas.booking import BookingCreate, BookingStatus, BookingUpdate
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.landlord import LandlordCreate, LandlordUpdate
from app.schemas.payment import PaymentCreate, PaymentStatus, PaymentUpdate
from app.schemas.photo import PhotoCreate
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate

# Mock location for testing
MOCK_LOCATION = Point(37.6173, 55.7558)  # Moscow coordinates


class TestUserSchemas:
    """Tests for User schema validation."""

    def test_user_create_valid(self) -> None:
        """Test creating a valid user."""
        user = UserCreate(
            email="test@example.com",
            phone_number="+1234567890",
            password_hash="securepass123",
            telegram_username="@testuser",
        )
        assert user.email == "test@example.com"

    def test_user_create_invalid_email(self) -> None:
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="invalid-email",
                phone_number="+1234567890",
                password="securepass123",
            )
        assert "email" in str(exc_info.value).lower()

    def test_user_create_short_password(self) -> None:
        """Test that password_hash shorter than 6 characters raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                phone_number="+1234567890",
                password="short",
            )
        assert "password" in str(exc_info.value).lower()

    def test_user_update_partial(self) -> None:
        """Test partial update schema."""
        update = UserUpdate(email="newemail@example.com")
        assert update.email == "newemail@example.com"
        assert update.phone_number is None
        assert update.password is None

    def test_user_read_from_attributes(self) -> None:
        """Test UserRead with from_attributes config."""

        class MockUser:
            id = 1
            email = "test@example.com"
            phone_number = "+1234567890"
            registration_date = datetime.now(tz=UTC)
            telegram_username = None

        user_read = UserRead.model_validate(MockUser())
        assert user_read.id == 1
        assert user_read.email == "test@example.com"


class TestApartmentSchemas:
    """Tests for Apartment schema validation."""

    def test_apartment_create_valid(self) -> None:
        """Test creating a valid apartment."""
        apartment = ApartmentCreate(
            name="Cozy Studio",
            description="A beautiful apartment",
            price_per_night=50.0,
            address="123 Main Street",
            location=MOCK_LOCATION,
            landlord_id=1,
        )
        assert apartment.name == "Cozy Studio"
        assert apartment.price_per_night == 50.0

    def test_apartment_create_negative_price(self) -> None:
        """Test that negative price raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ApartmentCreate(
                name="Test Apartment",
                price_per_night=-50.0,
                address="123 Main Street",
                location=MOCK_LOCATION,
                landlord_id=1,
            )
        assert "price_per_night" in str(exc_info.value).lower()

    def test_apartment_create_zero_price(self) -> None:
        """Test that zero price raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ApartmentCreate(
                name="Test Apartment",
                price_per_night=0,
                address="123 Main Street",
                location=MOCK_LOCATION,
                landlord_id=1,
            )
        assert "price_per_night" in str(exc_info.value).lower()

    def test_apartment_update_partial(self) -> None:
        """Test partial apartment update."""
        update = ApartmentUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.description is None
        assert update.price_per_night is None


class TestBookingSchemas:
    """Tests for Booking schema validation."""

    def test_booking_create_valid(self) -> None:
        """Test creating a valid booking."""
        booking = BookingCreate(
            start_date=datetime(2024, 1, 15, 14, 0, tzinfo=UTC),
            end_date=datetime(2024, 1, 20, 11, 0, tzinfo=UTC),
            cost=250.0,
            booking_status=BookingStatus.pending,
            landlord_id=1,
            client_id=1,
            apartment_id=1,
        )
        assert booking.cost == 250.0
        assert booking.booking_status == BookingStatus.pending

    def test_booking_status_enum(self) -> None:
        """Test booking status enumeration values."""
        assert BookingStatus.pending.value == "pending"
        assert BookingStatus.confirmed.value == "confirmed"
        assert BookingStatus.cancelled.value == "cancelled"

    def test_booking_create_negative_cost(self) -> None:
        """Test that negative cost raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            BookingCreate(
                start_date=datetime(2024, 1, 15, tzinfo=UTC),
                end_date=datetime(2024, 1, 20, tzinfo=UTC),
                cost=-100.0,
                booking_status=BookingStatus.pending,
                landlord_id=1,
                client_id=1,
                apartment_id=1,
            )
        assert "cost" in str(exc_info.value).lower()

    def test_booking_update_partial(self) -> None:
        """Test partial booking update."""
        update = BookingUpdate(booking_status=BookingStatus.confirmed)
        assert update.booking_status == BookingStatus.confirmed
        assert update.cost is None


class TestPaymentSchemas:
    """Tests for Payment schema validation."""

    def test_payment_create_valid(self) -> None:
        """Test creating a valid payment."""
        payment = PaymentCreate(
            amount=100.0,
            payment_status=PaymentStatus.pending,
            booking_id=1,
        )
        assert payment.amount == 100.0
        assert payment.payment_status == PaymentStatus.pending

    def test_payment_status_enum(self) -> None:
        """Test payment status enumeration values."""
        assert PaymentStatus.paid.value == "paid"
        assert PaymentStatus.pending.value == "pending"
        assert PaymentStatus.failed.value == "failed"

    def test_payment_create_negative_amount(self) -> None:
        """Test that negative amount raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentCreate(
                amount=-100.0,
                payment_status=PaymentStatus.pending,
                booking_id=1,
            )
        assert "amount" in str(exc_info.value).lower()

    def test_payment_update_partial(self) -> None:
        """Test partial payment update."""
        update = PaymentUpdate(payment_status=PaymentStatus.paid)
        assert update.payment_status == PaymentStatus.paid
        assert update.amount is None


class TestLandlordSchemas:
    """Tests for Landlord schema validation."""

    def test_landlord_create_valid(self) -> None:
        """Test creating a valid landlord."""
        landlord = LandlordCreate(
            first_name="John",
            last_name="Doe",
            user_id=1,
        )
        assert landlord.first_name == "John"
        assert landlord.user_id == 1

    def test_landlord_update_partial(self) -> None:
        """Test partial landlord update."""
        update = LandlordUpdate(first_name="Jane")
        assert update.first_name == "Jane"
        assert update.last_name is None


class TestClientSchemas:
    """Tests for Client schema validation."""

    def test_client_create_valid(self) -> None:
        """Test creating a valid client."""
        client = ClientCreate(
            first_name="Jane",
            last_name="Smith",
            user_id=1,
        )
        assert client.first_name == "Jane"
        assert client.user_id == 1

    def test_client_update_partial(self) -> None:
        """Test partial client update."""
        update = ClientUpdate(last_name="Doe")
        assert update.last_name == "Doe"
        assert update.first_name is None


class TestPhotoSchemas:
    """Tests for Photo schema validation."""

    def test_photo_create_valid(self) -> None:
        """Test creating a valid photo."""
        photo = PhotoCreate(
            url="https://example.com/photo.jpg",
            apartment_id=1,
        )
        assert photo.url == "https://example.com/photo.jpg"
        assert photo.apartment_id == 1

    def test_photo_create_long_url(self) -> None:
        """Test that URL exceeding max length raises error."""
        long_url = "https://example.com/" + "a" * 300
        with pytest.raises(ValidationError) as exc_info:
            PhotoCreate(
                url=long_url,
                apartment_id=1,
            )
        assert "url" in str(exc_info.value).lower()


class TestBalanceSchemas:
    """Tests for Balance schema validation."""

    def test_balance_create_valid(self) -> None:
        """Test creating a valid balance."""
        balance = BalanceCreate(
            amount=250.0,
            user_id=1,  # Теперь это обязательное поле вместо booking_i
        )
        assert balance.amount == 250.0
        assert balance.user_id == 1

    def test_balance_create_negative_amount(self) -> None:
        """Test that negative amount raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            BalanceCreate(
                amount=-100.0,
                user_id=1,
            )
        assert "amount" in str(exc_info.value).lower()

    def test_balance_create_zero_amount(self) -> None:
        """Test that zero amount raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            BalanceCreate(
                amount=0,
                user_id=1,
            )
        assert "amount" in str(exc_info.value).lower()

    def test_balance_update_partial(self) -> None:
        """Test partial balance update."""
        update = BalanceUpdate(amount=500.0)
        assert update.amount == 500.0


class TestReviewSchemas:
    """Tests for Review schema validation."""

    def test_review_create_valid(self) -> None:
        """Test creating a valid review."""
        review = ReviewCreate(
            rating=5,
            review="Excellent service!",
            booking_id=1,
            landlord_id=1,
            client_id=1,
            author_role="client",
        )
        assert review.rating == 5
        assert review.review == "Excellent service!"
        assert review.author_role == "client"

    def test_review_create_without_text(self) -> None:
        """Test creating a review without review text."""
        review = ReviewCreate(
            rating=4,
            review=None,
            booking_id=1,
            landlord_id=1,
            client_id=1,
            author_role="client",
        )
        assert review.rating == 4
        assert review.review is None

    def test_review_create_rating_too_low(self) -> None:
        """Test that rating below 1 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewCreate(
                rating=0,
                review="Bad",
                booking_id=1,
                landlord_id=1,
                client_id=1,
            )
        assert "rating" in str(exc_info.value).lower()

    def test_review_create_rating_too_high(self) -> None:
        """Test that rating above 5 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewCreate(
                rating=6,
                review="Too good",
                booking_id=1,
                landlord_id=1,
                client_id=1,
            )
        assert "rating" in str(exc_info.value).lower()

    def test_review_create_text_too_long(self) -> None:
        """Test that review text exceeding max length raises error."""
        long_text = "a" * 701
        with pytest.raises(ValidationError) as exc_info:
            ReviewCreate(
                rating=5,
                review=long_text,
                booking_id=1,
                landlord_id=1,
                client_id=1,
            )
        assert "review" in str(exc_info.value).lower()

    def test_review_update_partial(self) -> None:
        """Test partial review update."""
        update = ReviewUpdate(rating=4)
        assert update.rating == 4
        assert update.review is None
