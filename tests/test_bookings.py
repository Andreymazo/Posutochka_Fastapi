"""Tests for booking functionality with DATERANGE support."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.apartment import Apartment
from app.models.booking import Booking
from app.models.client import Client
from app.models.landlord import Landlord

import pytest
from httpx import AsyncClient
from app.models import Landlord, Client, Apartment

class TestBookingDateRange:
    """Tests for DATERANGE functionality in Booking model."""

    @pytest.mark.asyncio  # Обязательно: указывает pytest, что тест асинхронный
    async def test_create_booking_with_daterange(
        self,
        client: AsyncClient,  # Используем AsyncClient вместо TestClient
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test creating a booking with start_date and end_date (converted to DATERANGE)."""
        booking_data = {
            "start_date": "2026-03-15",  # Используем 2026 год
            "end_date": "2026-03-20",
            "cost": 250.0,
            "booking_status": "pending",
            "landlord_id": created_landlord.id,
            "client_id": created_client.id,
            "apartment_id": created_apartment.id,
        }

        # Обязательно добавляем await перед вызовом
        response = await client.post("/bookings/", json=booking_data)

        # Теперь AttributeError: 'coroutine' исчезнет
        assert response.status_code == 201
        data = response.json()
        assert data["start_date"] == "2026-03-15"
        assert data["end_date"] == "2026-03-20"
        assert data["cost"] == 250.0
        assert data["booking_status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_booking_returns_dates_from_range(
        self,
        client: AsyncClient,        # Используем асинхронный клиент
        db_session: AsyncSession,   # Используем асинхронную сессию
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test that getting a booking returns start_date and end_date from booking_period."""
        
        # 1. Создаем объект Range (используем 2026 год)
        booking_period = Range(date(2026, 4, 1), date(2026, 4, 5), bounds="[)")
        
        # 2. Создаем бронирование напрямую в базе
        booking = Booking(
            booking_period=booking_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id, 
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )
        
        # Асинхронно добавляем и коммитим
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)

        # 3. Выполняем асинхронный GET запрос (обязательно await)
        response = await client.get(f"/bookings/{booking.id}")

        # 4. Проверяем результат
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем, что роутер корректно вытащил даты из объекта Range
        assert data["start_date"] == "2026-04-01"
        assert data["end_date"] == "2026-04-05"
    
    @pytest.mark.asyncio
    async def test_update_booking_dates(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test updating booking dates (updates the DATERANGE)."""
        # 1. Создаем начальное бронирование (исправлено на 2026)
        booking_period = Range(date(2026, 5, 1), date(2026, 5, 5), bounds="[)")
        booking = Booking(
            booking_period=booking_period,
            cost=200.0,
            booking_status="pending",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        # 2. Обновляем дату окончания через PATCH запрос
        # В 2026 году мы ожидаем, что сервис корректно пересоберет Range
        update_data = {"end_date": "2026-05-10"}
        
        # Обязательно добавляем await
        response = await client.patch(f"/bookings/{booking.id}", json=update_data)

        # 3. Проверка результата
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем, что дата начала осталась прежней, а дата конца обновилась
        assert data["start_date"] == "2026-05-01"
        assert data["end_date"] == "2026-05-10"

        # Дополнительная проверка: убедимся, что в БД данные тоже обновились
        await db_session.refresh(booking)
        assert booking.booking_period.upper == date(2026, 5, 10)
      
    @pytest.mark.asyncio
    async def test_search_overlapping_bookings(
        self,
        db_session: AsyncSession,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test searching for apartments occupied on specific dates using DATERANGE overlap."""
        # 1. Создаем несколько бронирований (используем 2026 год)
        booking1_period = Range(date(2026, 6, 1), date(2026, 6, 5), bounds="[)")
        booking1 = Booking(
            booking_period=booking1_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )

        booking2_period = Range(date(2026, 6, 10), date(2026, 6, 15), bounds="[)")
        booking2 = Booking(
            booking_period=booking2_period,
            cost=250.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )

        db_session.add_all([booking1, booking2])
        await db_session.commit()

        # 2. Поиск бронирований, которые пересекаются с 3-7 июня (должен найти booking1)
        search_range = Range(date(2026, 6, 3), date(2026, 6, 7), bounds="[)")
        query = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range))
        
        result = await db_session.execute(query)
        occupied_apartments = result.scalars().all()

        assert created_apartment.id in occupied_apartments

        # 3. Поиск бронирований, которые пересекаются с 12-20 июня (должен найти booking2)
        search_range2 = Range(date(2026, 6, 12), date(2026, 6, 20), bounds="[)")
        query2 = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range2))
        
        result2 = await db_session.execute(query2)
        occupied_apartments2 = result2.scalars().all()

        assert created_apartment.id in occupied_apartments2

        # 4. Поиск бронирований, которые НЕ пересекаются (20-25 июня)
        search_range3 = Range(date(2026, 6, 20), date(2026, 6, 25), bounds="[)")
        query3 = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range3))
        
        result3 = await db_session.execute(query3)
        occupied_apartments3 = result3.scalars().all()

        assert created_apartment.id not in occupied_apartments3

    @pytest.mark.asyncio
    async def test_daterange_contains_date(
        self,
        db_session: AsyncSession,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test checking if a specific date is within a booking period."""
        # 1. Создаем бронирование на 1-5 июня 2026 года
        booking_period = Range(date(2026, 6, 1), date(2026, 6, 5), bounds="[)")
        booking = Booking(
            booking_period=booking_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
         # 2. Проверяем, входит ли 3 июня в период бронирования
        check_date = date(2026, 6, 3)
        # Добавляем фильтр по apartment_id, чтобы не цеплять чужие брони из базы
        query = (
            select(Booking)
            .where(
                Booking.apartment_id == created_apartment.id, # Фильтр по нашей квартире
                Booking.booking_period.contains(check_date)
            )
        )
        result = await db_session.execute(query)
        found_booking = result.scalars().first()

        assert found_booking is not None
        # Теперь мы уверены, что нашли именно наше бронирование
        assert found_booking.id == booking.id
        # 3. Проверяем 6 июня (не должно входить)
        check_date2 = date(2026, 6, 6)
        query2 = select(Booking).where(Booking.booking_period.contains(check_date2))
        result2 = await db_session.execute(query2)
        found_booking2 = result2.scalars().first()
        assert found_booking2 is None     
    
    @pytest.mark.asyncio
    async def test_daterange_bounds_exclusive_end(
        self,
        db_session: AsyncSession,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test that DATERANGE uses [) bounds (start inclusive, end exclusive)."""
        # 1. Создаем бронирование (используем июль 2026)
        booking_period = Range(date(2026, 7, 1), date(2026, 7, 5), bounds="[)")
        booking = Booking(
            booking_period=booking_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)

        # 2. Проверяем даты
        assert booking.booking_period.lower == date(2026, 7, 1)
        assert booking.booking_period.upper == date(2026, 7, 5)

        # 3. Проверяем флаги включения границ
        # lower_inc ( [ ) -> True (включено)
        assert booking.booking_period.lower_inc is True
        
        # upper_inc ( ) ) -> False (исключено)
        # Это означает, что 5-е число — это момент выезда, и оно не занято для следующего гостя
        assert booking.booking_period.upper_inc is False

    @pytest.mark.asyncio
    async def test_get_all_bookings_for_apartment(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test retrieving all bookings for a specific apartment."""
        # 1. Создаем несколько бронирований для одного апартамента (используем август 2026)
        booking1_period = Range(date(2026, 8, 1), date(2026, 8, 5), bounds="[)")
        booking1 = Booking(
            booking_period=booking1_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )

        booking2_period = Range(date(2026, 8, 10), date(2026, 8, 15), bounds="[)")
        booking2 = Booking(
            booking_period=booking2_period,
            cost=250.0,
            booking_status="pending",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )

        db_session.add_all([booking1, booking2])
        await db_session.commit()

        # 2. Получаем все бронирования через API с фильтром (ОБЯЗАТЕЛЬНО await)
        response = await client.get(f"/bookings/?apartment_id={created_apartment.id}")

        # 3. Проверки
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем количество (может быть больше 2, если в базе остался "мусор" от прошлых тестов)
        assert len(data) >= 2
        
        # Проверяем, что в ответе корректно распарсены даты из Range
        assert any(b["start_date"] == "2026-08-01" for b in data)
        assert any(b["start_date"] == "2026-08-10" for b in data)
        assert all("start_date" in b and "end_date" in b for b in data)

# class TestBookingDateRange:
#     """Tests for DATERANGE functionality in Booking model."""

#     def test_create_booking_with_daterange(
#         self,
#         client: TestClient,
#         created_landlord: Landlord,
#         created_client: Client,
#         created_apartment: Apartment,
#     ) -> None:
#         """Test creating a booking with start_date and end_date (converted to DATERANGE)."""
#         booking_data = {
#             "start_date": "2024-03-15",
#             "end_date": "2024-03-20",
#             "cost": 250.0,
#             "booking_status": "pending",
#             "landlord_id": created_landlord.id,
#             "client_id": created_client.id,
#             "apartment_id": created_apartment.id,
#         }

#         response = client.post("/bookings/", json=booking_data)

#         assert response.status_code == 201
#         data = response.json()
#         assert data["start_date"] == "2024-03-15"
#         assert data["end_date"] == "2024-03-20"
#         assert data["cost"] == 250.0
#         assert data["booking_status"] == "pending"

    # def test_get_booking_returns_dates_from_range(
    #     self,
    #     client: TestClient,
    #     db_session: Session,
    #     created_landlord: Landlord,
    #     created_client: Client,
    #     created_apartment: Apartment,
    # ) -> None:
    #     """Test that getting a booking returns start_date and end_date from booking_period."""
    #     # Create booking directly in database with Range
    #     booking_period = Range(date(2024, 4, 1), date(2024, 4, 5), bounds="[)")
    #     booking = Booking(
    #         booking_period=booking_period,
    #         cost=200.0,
    #         booking_status="confirmed",
    #         landlord_id=created_landlord.id, 
    #         client_id=created_client.id,
    #         apartment_id=created_apartment.id,
    #     )
    #     db_session.add(booking)
    #     db_session.commit()
    #     db_session.refresh(booking)

    #     response = client.get(f"/bookings/{booking.id}")

    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["start_date"] == "2024-04-01"
    #     assert data["end_date"] == "2024-04-05"

    # def test_update_booking_dates(
    #     self,
    #     client: TestClient,
    #     db_session: Session,
    #     created_landlord: Landlord,
    #     created_client: Client,
    #     created_apartment: Apartment,
    # ) -> None:
    #     """Test updating booking dates (updates the DATERANGE)."""
    #     # Create initial booking
    #     booking_period = Range(date(2024, 5, 1), date(2024, 5, 5), bounds="[)")
    #     booking = Booking(
    #         booking_period=booking_period,
    #         cost=200.0,
    #         booking_status="pending",
    #         landlord_id=created_landlord.id,
    #         client_id=created_client.id,
    #         apartment_id=created_apartment.id,
    #     )
    #     db_session.add(booking)
    #     db_session.commit()
    #     db_session.refresh(booking)

    #     # Update end_date
    #     update_data = {"end_date": "2024-05-10"}
    #     response = client.patch(f"/bookings/{booking.id}", json=update_data)

    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["start_date"] == "2024-05-01"
    #     assert data["end_date"] == "2024-05-10"

    # def test_search_overlapping_bookings(
    #     self,
    #     db_session: Session,
    #     created_landlord: Landlord,
    #     created_client: Client,
    #     created_apartment: Apartment,
    # ) -> None:
    #     """Test searching for apartments occupied on specific dates using DATERANGE overlap."""
    #     # Create several bookings for the same apartment
    #     booking1_period = Range(date(2024, 6, 1), date(2024, 6, 5), bounds="[)")
    #     booking1 = Booking(
    #         booking_period=booking1_period,
    #         cost=200.0,
    #         booking_status="confirmed",
    #         landlord_id=created_landlord.id,
    #         client_id=created_client.id,
    #         apartment_id=created_apartment.id,
    #     )

    #     booking2_period = Range(date(2024, 6, 10), date(2024, 6, 15), bounds="[)")
    #     booking2 = Booking(
    #         booking_period=booking2_period,
    #         cost=250.0,
    #         booking_status="confirmed",
    #         landlord_id=created_landlord.id,
    #         client_id=created_client.id,
    #         apartment_id=created_apartment.id,
    #     )

    #     db_session.add_all([booking1, booking2])
    #     db_session.commit()

    #     # Search for bookings that overlap with June 3-7 (should find booking1)
    #     search_range = Range(date(2024, 6, 3), date(2024, 6, 7), bounds="[)")
    #     query = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range))
    #     occupied_apartments = db_session.execute(query).scalars().all()

    #     assert created_apartment.id in occupied_apartments

    #     # Search for bookings that overlap with June 12-20 (should find booking2)
    #     search_range2 = Range(date(2024, 6, 12), date(2024, 6, 20), bounds="[)")
    #     query2 = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range2))
    #     occupied_apartments2 = db_session.execute(query2).scalars().all()

    #     assert created_apartment.id in occupied_apartments2

    #     # Search for bookings that don't overlap (June 20-25)
    #     search_range3 = Range(date(2024, 6, 20), date(2024, 6, 25), bounds="[)")
    #     query3 = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range3))
    #     occupied_apartments3 = db_session.execute(query3).scalars().all()

    #     assert created_apartment.id not in occupied_apartments3

    # def test_daterange_contains_date(
    #     self,
    #     db_session: Session,
    #     created_landlord: Landlord,
    #     created_client: Client,
    #     created_apartment: Apartment,
    # ) -> None:
    #     """Test checking if a specific date is within a booking period."""
    #     # Create booking for June 1-5
    #     booking_period = Range(date(2024, 6, 1), date(2024, 6, 5), bounds="[)")
    #     booking = Booking(
    #         booking_period=booking_period,
    #         cost=200.0,
    #         booking_status="confirmed",
    #         landlord_id=created_landlord.id,
    #         client_id=created_client.id,
    #         apartment_id=created_apartment.id,
    #     )
    #     db_session.add(booking)
    #     db_session.commit()
    #     db_session.refresh(booking)

    #     # Check if June 3 is within the booking period
    #     check_date = date(2024, 6, 3)
    #     query = select(Booking).where(Booking.booking_period.contains(check_date))
    #     result = db_session.execute(query).scalars().first()

    #     assert result is not None
    #     assert result.id == booking.id

    #     # Check if June 6 is within the booking period (should not be, end is exclusive)
    #     check_date2 = date(2024, 6, 6)
    #     query2 = select(Booking).where(Booking.booking_period.contains(check_date2))
    #     result2 = db_session.execute(query2).scalars().first()

    #     assert result2 is None

    # def test_daterange_bounds_exclusive_end(
    #     self,
    #     db_session: Session,
    #     created_landlord: Landlord,
    #     created_client: Client,
    #     created_apartment: Apartment,
    # ) -> None:
    #     """Test that DATERANGE uses [) bounds (start inclusive, end exclusive)."""
    #     # Create booking with [) bounds
    #     booking_period = Range(date(2024, 7, 1), date(2024, 7, 5), bounds="[)")
    #     booking = Booking(
    #         booking_period=booking_period,
    #         cost=200.0,
    #         booking_status="confirmed",
    #         landlord_id=created_landlord.id,
    #         client_id=created_client.id,
    #         apartment_id=created_apartment.id,
    #     )
    #     db_session.add(booking)
    #     db_session.commit()
    #     db_session.refresh(booking)

    #     # Verify the start date is included
    #     assert booking.booking_period.lower == date(2024, 7, 1)
    #     assert booking.booking_period.upper == date(2024, 7, 5)

    #     # Check that July 1 is included
    #     assert booking.booking_period.lower_inc is True
    #     # Check that July 5 is excluded
    #     assert booking.booking_period.upper_inc is False

    # def test_get_all_bookings_for_apartment(
    #     self,
    #     client: TestClient,
    #     db_session: Session,
    #     created_landlord: Landlord,
    #     created_client: Client,
    #     created_apartment: Apartment,
    # ) -> None:
    #     """Test retrieving all bookings for a specific apartment."""
    #     # Create multiple bookings
    #     booking1_period = Range(date(2024, 8, 1), date(2024, 8, 5), bounds="[)")
    #     booking1 = Booking(
    #         booking_period=booking1_period,
    #         cost=200.0,
    #         booking_status="confirmed",
    #         landlord_id=created_landlord.id,
    #         client_id=created_client.id,
    #         apartment_id=created_apartment.id,
    #     )

    #     booking2_period = Range(date(2024, 8, 10), date(2024, 8, 15), bounds="[)")
    #     booking2 = Booking(
    #         booking_period=booking2_period,
    #         cost=250.0,
    #         booking_status="pending",
    #         landlord_id=created_landlord.id,
    #         client_id=created_client.id,
    #         apartment_id=created_apartment.id,
    #     )

    #     db_session.add_all([booking1, booking2])
    #     db_session.commit()

    #     # Get all bookings for the apartment
    #     response = client.get(f"/bookings/?apartment_id={created_apartment.id}")

    #     assert response.status_code == 200
    #     data = response.json()
    #     assert len(data) == 2
    #     assert all("start_date" in booking and "end_date" in booking for booking in data)
