"""Tests for booking functionality with DATERANGE support."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Apartment, Client, Landlord
from app.models.apartment import Apartment
from app.models.booking import Booking
from app.models.client import Client
from app.models.landlord import Landlord

from unittest.mock import patch, AsyncMock


class TestBookingDateRange:
    """Tests for DATERANGE functionality in Booking model."""
    
    @pytest.mark.asyncio
    async def test_create_booking_with_daterange(
        self,
        client: AsyncClient,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        booking_data = {
            "start_date": "2026-03-15",
            "end_date": "2026-03-20",
            "cost": 250.0,
            "booking_status": "pending",
            "landlord_id": created_landlord.id,
            "client_id": created_client.id,
            "apartment_id": created_apartment.id,
        }
    
        # ПАТЧИМ задачу уведомлений, чтобы она не лезла в базу параллельно
        with patch("app.routers.bookings.send_booking_notification") as mock_task:
            response = await client.post("/bookings/", json=booking_data)
            
        assert response.status_code == 201


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
