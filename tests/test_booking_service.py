import pytest
from datetime import date, timedelta
from fastapi import HTTPException
from app.services.booking_service import BookingService
from app.schemas.booking import BookingCreate, BookingStatus, BookingUpdate
from app.services.availability_service import AvailabilityService
from fastapi import HTTPException, status

@pytest.mark.asyncio
async def test_create_booking_busy_dates(db_session, created_apartment, mock_landlord_profile):
    """Проверка ошибки, если даты пересекаются с блокировкой."""
    start = date(2026, 8, 1)
    end = date(2026, 8, 5)
    
    # Создаем блокировку
    await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, start, end, is_blocked=True
    )
    await db_session.commit() # Фиксируем в БД, чтобы сервис увидел запись
    
    booking_data = BookingCreate(
        apartment_id=created_apartment.id,
        check_in=start,
        check_out=end,
        cost=1000.0,
        booking_status="pending", # Используем строку из вашей модели
        landlord_id=mock_landlord_profile.id,
        client_id=1 
    )
    
    with pytest.raises(HTTPException) as exc:
        await BookingService.create_new_booking(db_session, booking_data, client_id=999)
    assert exc.value.status_code == 400
    assert "заняты" in exc.value.detail

@pytest.mark.asyncio
async def test_create_booking_min_stay_violation(db_session, created_apartment, mock_landlord_profile):
    """Проверка нарушения правила минимального срока проживания."""
    # Устанавливаем правило: минимум 5 дней
    await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, date(2026, 9, 1), date(2026, 9, 30),
        is_blocked=False, min_stay_days=5
    )
    await db_session.commit()
    
    # Пытаемся забронировать на 2 дня (10-е по 12-е)
    booking_data = BookingCreate(
        apartment_id=created_apartment.id,
        check_in=date(2026, 9, 10),
        check_out=date(2026, 9, 12),
        cost=500.0,
        booking_status="pending", # Строка из вашей модели
        landlord_id=mock_landlord_profile.id,
        client_id=1 
    )
    
    with pytest.raises(HTTPException) as exc:
        await BookingService.create_new_booking(db_session, booking_data, client_id=999)
    assert exc.value.status_code == 400
    assert "Минимальный срок проживания" in exc.value.detail

@pytest.mark.asyncio
async def test_get_bookings_filters(db_session, created_booking):
    """Проверка работы всех фильтров в списке броней."""
    # Тест фильтра по landlord_id
    res = await BookingService.get_bookings(db_session, landlord_id=created_booking.landlord_id)
    assert len(res) >= 1
    
    # Тест фильтра по client_id
    res = await BookingService.get_bookings(db_session, client_id=created_booking.client_id)
    assert len(res) >= 1
    
    # Тест фильтра по apartment_id
    res = await BookingService.get_bookings(db_session, apartment_id=created_booking.apartment_id)
    assert len(res) >= 1
    
    # Тест пагинации
    res = await BookingService.get_bookings(db_session, limit=1)
    assert len(res) == 1
@pytest.mark.asyncio
async def test_get_booking_not_found(db_session):
    """Проверка 404 при поиске несуществующей брони."""
    with pytest.raises(HTTPException) as exc:
        await BookingService.get_booking_by_id(db_session, 999999)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_create_booking_min_stay_error_trigger(db_session, created_apartment, mock_landlord_profile):
    """Тест специально для срабатывания ошибки минимального срока."""
    # Создаем правило: минимум 10 ночей
    from app.services.availability_service import AvailabilityService
    await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, date(2026, 1, 1), date(2026, 1, 31),
        is_blocked=False, min_stay_days=10
    )
    await db_session.commit()

    # Бронируем только на 2 ночи
    booking_data = BookingCreate(
        apartment_id=created_apartment.id,
        check_in=date(2026, 1, 5),
        check_out=date(2026, 1, 7),
        cost=100.0,
        booking_status="pending",
        landlord_id=mock_landlord_profile.id,
        client_id=1
    )

    with pytest.raises(HTTPException) as exc:
        await BookingService.create_new_booking(db_session, booking_data, client_id=1)
    assert exc.value.status_code == 400
    assert "Минимальный срок проживания" in exc.value.detail


@pytest.mark.asyncio
async def test_update_booking_status(db_session, created_booking):
    """Тест метода update_booking."""
    update_data = BookingUpdate(booking_status="confirmed")
    
    updated = await BookingService.update_booking(
        db_session, created_booking.id, update_data
    )
    
    assert updated.booking_status == "confirmed"
    assert updated.id == created_booking.id
@pytest.mark.asyncio
async def test_get_bookings_apartment_filter(db_session, created_booking):
    """Закрываем строку 159: фильтр по квартире."""
    res = await BookingService.get_bookings(
        db_session, apartment_id=created_booking.apartment_id
    )
    assert len(res) >= 1
    assert res[0].apartment_id == created_booking.apartment_id

from app.models import Landlord
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_booking_success_and_min_stay_pass(
    db_session, 
    created_apartment, 
    mock_landlord_profile, 
    created_client # <--- Используем существующую фикстуру
):
    """Закрывает ветки 91->90 и 97-119 (успешный путь)."""
    
    # 1. Получаем ID лендлорда (т.к. mock_landlord_profile - это User)
    res_l = await db_session.execute(
        select(Landlord).where(Landlord.user_id == mock_landlord_profile.id)
    )
    landlord_record = res_l.scalar_one()

    # 2. Создаем правило доступности (минимум 3 дня)
    await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, date(2026, 3, 1), date(2026, 3, 31),
        is_blocked=False, min_stay_days=3
    )
    await db_session.commit()

    # 3. Бронируем с реальными ID. 
    # created_client уже содержит правильный id из таблицы client
    booking_data = BookingCreate(
        apartment_id=created_apartment.id,
        check_in=date(2026, 3, 10),
        check_out=date(2026, 3, 14),
        cost=400.0,
        booking_status="pending",
        landlord_id=landlord_record.id,
        client_id=created_client.id  
    )
    
    booking = await BookingService.create_new_booking(
        db_session, 
        booking_data, 
        client_id=created_client.id
    )
    
    assert booking.id is not None
    assert booking.booking_period.lower == date(2026, 3, 10)


@pytest.mark.asyncio
async def test_update_booking_full(db_session, created_booking):
    """Закрывает строки 228-245: обновление дат и параметров."""
    # Обновляем даты и стоимость
    new_start = date(2026, 11, 20)
    new_end = date(2026, 11, 25)
    update_data = BookingUpdate(
        check_in=new_start,
        check_out=new_end,
        cost=999.99
    )
    
    updated = await BookingService.update_booking(
        db_session, created_booking.id, update_data
    )
    
    assert updated.cost == 999.99
    assert updated.booking_period.lower == new_start
    assert updated.booking_period.upper == new_end

@pytest.mark.asyncio
async def test_get_bookings_all_filters_combined(db_session, created_booking):
    """Дополнительно закрываем ветки фильтрации."""
    res = await BookingService.get_bookings(
        db_session, 
        landlord_id=created_booking.landlord_id,
        client_id=created_booking.client_id,
        apartment_id=created_booking.apartment_id
    )
    assert len(res) >= 1

@pytest.mark.asyncio
async def test_get_booking_by_id_final_coverage(db_session):
    """Финальный тест для закрытия строк 267-269 (Exception branch)."""
    
    # Пытаемся получить бронь с ID, которого точно нет
    invalid_id = 999999
    
    with pytest.raises(HTTPException) as exc:
        await BookingService.get_booking_by_id(db_session, invalid_id)
    
    # Проверяем детали, чтобы убедиться, что сработал именно тот код
    assert exc.value.status_code == 404
    assert exc.value.detail == "Booking not found"

@pytest.mark.asyncio
async def test_get_booking_by_id_absolute_coverage(db_session, created_booking):
    """Тест для гарантированного закрытия веток 267-269."""
    
    # Путь 1: Успешное получение (закрывает строку 269)
    existing_booking = await BookingService.get_booking_by_id(db_session, created_booking.id)
    assert existing_booking.id == created_booking.id

    # Путь 2: Ошибка (закрывает строки 267-268)
    with pytest.raises(HTTPException) as exc:
        await BookingService.get_booking_by_id(db_session, 888888) # Заведомо ложный ID
    
    assert exc.value.status_code == 404
    assert exc.value.detail == "Booking not found"

@pytest.mark.asyncio
async def test_delete_and_verify_booking(db_session, created_booking):
    """Тест проверяет удаление и корректную обработку 404 ошибки после удаления."""
    
    # 1. Удаляем бронирование
    await BookingService.delete_booking(db_session, created_booking.id)
    
    # 2. Проверяем, что при попытке получить удаленное бронирование выбрасывается 404
    with pytest.raises(HTTPException) as excinfo:
        await BookingService.get_booking_by_id(db_session, created_booking.id)
    
    # Дополнительно проверяем код статуса и сообщение
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert excinfo.value.detail == "Booking not found"
# pytest --cov=app.services.booking_service --cov-report=term-missing tests/test_booking_service.py
