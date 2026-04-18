"""Tests for Pydantic schemas validation."""

from datetime import UTC, datetime

from datetime import date
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
from app.schemas.apartment import ApartmentRead
from geoalchemy2.elements import WKBElement


# Mock location for testing
MOCK_LOCATION = Point(37.6173, 55.7558)  # Moscow coordinates



class TestUserSchemas:
    """Tests for User schema validation (Updated for 2026)."""

    def test_user_create_valid(self) -> None:
        """Test creating a valid user with all required fields."""
        user = UserCreate(
            email="test@example.com",
            phone_number="+79991234567",
            password="securepass123",
            first_name="иван",    # Проверим заодно капитализацию
            last_name="иванов",
            telegram_username="@testuser",
            role="user"
        )
        
        assert user.email == "test@example.com"
        assert user.phone_number == "+79991234567"
        # Проверяем работу вашего валидатора capitalize_names
        assert user.first_name == "Иван" 
        assert user.last_name == "Иванов"
        assert user.password == "securepass123"

    def test_user_create_invalid_email(self) -> None:
        """Test validation error for invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                phone_number="+79991234567",
                password="password123",
                first_name="Иван",
                last_name="Иванов"
            )

    def test_user_create_missing_required_fields(self) -> None:
        """Test validation error when names are missing."""
        with pytest.raises(ValidationError) as exc:
            # Не передаем обязательные теперь first_name и last_name
            UserCreate(
                email="test@example.com",
                phone_number="+79991234567",
                password="password123"
            )
        # Проверяем, что ошибка именно по именам
        errors = exc.value.errors()
        field_names = [err['loc'][0] for err in errors]
        assert 'first_name' in field_names
        assert 'last_name' in field_names

    def test_user_create_short_password(self) -> None:
        """Test that password shorter than 6 characters raises error."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                phone_number="+79991234567",
                password="short",      # < 6 символов
                first_name="Иван",     # Обязательные поля
                last_name="Иванов"
            )
        assert "password" in str(exc_info.value).lower()

    def test_user_update_partial(self) -> None:
        """Test partial update schema."""
        # В UserUpdate все поля опциональны (Optional), поэтому тут все ок
        update = UserUpdate(email="newemail@example.com")
        assert update.email == "newemail@example.com"
        assert update.phone_number is None
        assert update.first_name is None  # Проверьте наличие в UserUpdate

    def test_user_read_from_attributes(self) -> None:
        """Test UserRead with from_attributes config."""
        from datetime import datetime, UTC

        class MockUser:
            id = 1
            email = "test@example.com"
            phone_number = "+79991234567"
            first_name = "Иван"         # Добавлено
            last_name = "Иванов"        # Добавлено
            registration_date = datetime.now(tz=UTC)
            telegram_username = None

        # В Pydantic V2 используем model_validate
        user_read = UserRead.model_validate(MockUser())
        assert user_read.id == 1
        assert user_read.first_name == "Иван"
        
class TestBookingSchemas:
    """Tests for Booking schema validation."""

    def test_booking_create_valid(self) -> None:
        """Test creating a valid booking."""
        from datetime import date

        booking = BookingCreate(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 20),
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


class TestBookingSchemas:
    """Tests for Booking schema validation (Updated 2026)."""

    def test_booking_create_valid(self) -> None:
        """Test creating a valid booking with 2026 dates."""
        from datetime import date

        # Используем даты из февраля 2026 года
        booking = BookingCreate(
            check_in=date(2026, 2, 15), 
            check_out=date(2026, 2, 20),  
            cost=250.0,
            booking_status=BookingStatus.pending,
            landlord_id=1,
            client_id=1,
            apartment_id=1,
        )
        assert booking.cost == 250.0
        assert booking.booking_status == BookingStatus.pending

    def test_booking_create_valid_from_dict(self):
        """Тест создания схемы со всеми обязательными полями."""
        data = {
            "check_in": date(2026, 1, 1),
            "check_out": date(2026, 1, 2),
            "cost": 500.0,
            "booking_status": "confirmed",
            "landlord_id": 1,
            "client_id": 1,
            "apartment_id": 1
        }
        # В Pydantic V2 рекомендуется использовать BookingCreate(**data) 
        # или BookingCreate.model_validate(data)
        obj = BookingCreate(**data)
        assert obj.cost == 500.0
        assert obj.check_in < obj.check_out 


    def test_booking_status_enum(self) -> None:
        """Test booking status enumeration values."""
        assert BookingStatus.pending == "pending"
        assert BookingStatus.confirmed == "confirmed"
        assert BookingStatus.cancelled == "cancelled"

    def test_booking_create_negative_cost(self) -> None:
        """Test that negative cost raises validation error."""
        from datetime import date
        with pytest.raises(ValidationError) as exc_info:
            BookingCreate(
                start_date=date(2026, 2, 15),
                end_date=date(2026, 2, 20),
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

from pydantic import ValidationError
import pytest

class TestLandlordSchemas:
    """Tests for Landlord schema validation (Updated 2026)."""

    def test_landlord_create_valid(self) -> None:
        """Test creating a valid landlord."""
        # Теперь передаем только user_id, так как ФИО в User
        landlord = LandlordCreate(
            user_id=1,
        )
        assert landlord.user_id == 1

    def test_landlord_update_partial(self) -> None:
        """Test partial landlord update."""
        # Обновляем специфичные поля Landlord (если они есть), 
        # здесь ФИО больше не должно быть.
        update = LandlordUpdate() 
        assert update is not None


class TestClientSchemas:
    """Tests for Client schema validation (Updated 2026)."""

    def test_client_create_valid(self) -> None:
        """Test creating a valid client."""
        # Теперь передаем только user_id
        client = ClientCreate(
            user_id=1,
        )
        assert client.user_id == 1

    def test_client_update_partial(self) -> None:
        """Test partial client update."""
        # Убираем проверку на first_name/last_name, так как их нет в ClientUpdate
        update = ClientUpdate()
        assert update is not None


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
        # Убедитесь, что в PhotoCreate стоит Field(..., max_length=255)
        long_url = "https://example.com/" + "a" * 300
        with pytest.raises(ValidationError) as exc_info:
            PhotoCreate(
                url=long_url,
                apartment_id=1,
            )
        assert "url" in str(exc_info.value).lower()

class TestBalanceSchemas:
    """Тесты валидации схем баланса (2026)."""

    def test_balance_create_valid(self) -> None:
        """Проверка создания валидного баланса."""
        balance = BalanceCreate(
            current_balance=250.0,
            user_id=1
        )
        assert float(balance.current_balance) == 250.0
        assert balance.user_id == 1

    def test_balance_create_negative_current_balance(self) -> None:
        """Проверка, что отрицательный баланс вызывает ошибку."""
        with pytest.raises(ValidationError) as exc_info:
            BalanceCreate(
                current_balance=-100.0,
                user_id=1,
            )
        assert "current_balance" in str(exc_info.value).lower()

    def test_balance_update_partial(self) -> None:
        """Проверка частичного обновления баланса."""
        update = BalanceUpdate(current_balance=500.0)
        assert float(update.current_balance) == 500.0
class TestReviewSchemas:
    """Тесты валидации схем отзывов."""

    def test_review_create_valid(self) -> None:
        """Создание валидного отзыва."""
        review = ReviewCreate(
            rating=5,
            review="Excellent service!",
            booking_id=1,
            landlord_id=1,
            client_id=1,
            author_role="client",
        )
        assert review.rating == 5
        assert review.author_role == "client"

    def test_review_create_rating_too_high(self) -> None:
        """Проверка, что рейтинг выше 5 вызывает ошибку."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewCreate(
                rating=6,
                review="Too good",
                booking_id=1,
                landlord_id=1,
                client_id=1,
                author_role="client"
            )
        assert "rating" in str(exc_info.value).lower()

    def test_review_create_text_too_long(self) -> None:
        """Проверка ограничения длины текста (например, 700 символов)."""
        long_text = "a" * 701
        with pytest.raises(ValidationError) as exc_info:
            ReviewCreate(
                rating=5,
                review=long_text,
                booking_id=1,
                landlord_id=1,
                client_id=1,
                author_role="client"
            )
        assert "review" in str(exc_info.value).lower()


    def test_review_update_partial(self) -> None:
        """Test partial review update."""
        update = ReviewUpdate(rating=4)
        assert update.rating == 4
        assert update.review is None



def test_apartment_read_handle_dal_types_coverage():
    """Закрывает строки 65-67 в app/schemas/apartment.py через ApartmentRead."""
    
    # Базовые данные для всех тестов
    base_data = {
        "id": 1,
        "name": "Test",
        "price_per_night": 100.0,
        "address": "Address",
        "landlord_id": 1,
        "photos": []
    }

    # 1. Покрываем строку 65 (WKBElement)
    # Используем валидный WKB для POINT(1 1)
    valid_wkb = b'\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0?\x00\x00\x00\x00\x00\x00\xf0?'
    data_wkb = {**base_data, "location": WKBElement(data=valid_wkb)}
    obj_wkb = ApartmentRead.model_validate(data_wkb)
    assert obj_wkb.location.x == 1.0

    # 2. Покрываем строку 66 (WKT String)
    data_wkt = {**base_data, "location": "POINT(30 60)"}
    obj_wkt = ApartmentRead.model_validate(data_wkt)
    assert obj_wkt.location.x == 30.0

    # 3. Покрываем строку 67 (return v)
    # Передаем уже готовый объект Point. Он не WKB и не строка POINT.
    data_obj = {**base_data, "location": Point(10, 20)}
    obj_point = ApartmentRead.model_validate(data_obj)
    assert obj_point.location.x == 10.0
# from geoalchemy2.shape import from_shape
# from shapely.geometry import Point
# from geoalchemy2.elements import WKBElement

# def test_apartment_read_handle_geo_types():
#     """Тестирование десериализации различных форматов гео-данных (WKB, WKT, Obj)."""
    
#     base_data = {
#         "id": 1,
#         "name": "Test Apartment",
#         "price_per_night": 100.0,
#         "address": "Address",
#         "landlord_id": 1,
#         "photos": [],
#         "description": "Test"
#     }

#     # 1. Тест WKBElement (как данные приходят из БД через SQLAlchemy)
#     # Используем POINT(1 1)
#     point_obj = Point(1.0, 1.0)
#     wkb_element = from_shape(point_obj) 
    
#     data_wkb = {**base_data, "location": wkb_element}
#     obj_wkb = ApartmentRead.model_validate(data_wkb)
#     assert obj_wkb.location.x == 1.0

#     # 2. Тест WKT String (текстовый формат)
#     data_wkt = {**base_data, "location": "POINT(30 60)"}
#     obj_wkt = ApartmentRead.model_validate(data_wkt)
#     assert obj_wkt.location.x == 30.0

#     # 3. Тест прямого объекта Shapely Point
#     data_obj = {**base_data, "location": Point(10, 20)}
#     obj_point = ApartmentRead.model_validate(data_obj)
#     assert obj_point.location.x == 10.0

def test_booking_schema_date_equal_validation():
    data = {
        "apartment_id": 1,
        "landlord_id": 1,
        "client_id": 1,
        "check_in": date(2026, 1, 20),
        "check_out": date(2026, 1, 20),
        "cost": 1000.0,
        "booking_status": "pending"
    }
    with pytest.raises(ValidationError) as exc:
        BookingCreate(**data)
    
    # Ищем само сообщение, которое мы написали в валидаторе
    assert "Дата выезда должна быть позже даты заезда" in str(exc.value)

from datetime import date
from psycopg.types.range import Range
from app.schemas.booking import BookingRead, BookingCreate

def test_booking_read_split_range_coverage():
    """Закрывает переход 57->61 в app/schemas/booking.py."""
    
    # Сценарий А: Объекта с периодом НЕТ (закрывает ветку пропуска if)
    data_no_period = {
        "id": 1,
        "landlord_id": 1,
        "client_id": 1,
        "apartment_id": 1,
        "check_in": date(2026, 1, 1),
        "check_out": date(2026, 1, 2),
        "cost": 100.0,
        "booking_status": "confirmed",
        "payments": []
    }
    # Прямая валидация словаря (без атрибута booking_period)
    obj = BookingRead.model_validate(data_no_period)
    assert obj.id == 1

    # Сценарий Б: Объект с периодом ЕСТЬ (для полноты)
    class MockBooking:
        id = 2
        landlord_id = 1
        client_id = 1
        apartment_id = 1
        cost = 150.0
        booking_status = "pending"
        booking_period = Range(date(2026, 2, 1), date(2026, 2, 5))
        payments = []

    obj_from_orm = BookingRead.model_validate(MockBooking())
    assert obj_from_orm.check_in == date(2026, 2, 1)

def test_booking_create_valid():
    """Тест создания схемы со всеми обязательными полями."""
    data = {
        "check_in": date(2026, 1, 1),
        "check_out": date(2026, 1, 2),
        "cost": 500.0,
        "booking_status": "confirmed",
        "landlord_id": 1,
        "client_id": 1,
        "apartment_id": 1
    }
    obj = BookingCreate(**data)
    assert obj.cost == 500.0