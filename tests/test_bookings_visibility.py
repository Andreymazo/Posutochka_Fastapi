import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.services.booking_service import BookingService
from app.schemas.booking import BookingCreate, BookingStatus

@pytest.mark.asyncio
async def test_booking_blocks_apartment_visibility(
    client, 
    db_session, 
    created_apartment, 
    created_client,        # Юзер, который делает бронь
    mock_client_profile    # Другой юзер, который ищет квартиру
):
    """
    Интеграционный тест:
    1. Проверяем, что квартира видна в поиске.
    2. Создаем бронь через BookingService.
    3. Проверяем, что квартира исчезла из поиска на эти даты для другого юзера.
    """
    # Устанавливаем даты на февраль 2026
    check_in = date(2026, 2, 10)
    check_out = date(2026, 2, 15)
    
    # ПАРАМЕТРЫ ПОИСКА (точка из твоей фикстуры апартамента)
    search_params = {
        "lat": 55.7558, 
        "lon": 37.6173, 
        "radius": 1000,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat()
    }

    # ШАГ 1: Квартира изначально свободна и видна
    response = await client.get("/apartments/search", params=search_params)
    assert response.status_code == 200
    assert any(a["id"] == created_apartment.id for a in response.json()), "Квартира должна быть видна"

    # ШАГ 2: Создаем бронь
    # Это вызовет твою новую логику в BookingService, которая создаст ApartmentAvailability
    booking_data = BookingCreate(
        apartment_id=created_apartment.id,
        landlord_id=created_apartment.landlord_id,
        client_id=created_client.id,
        start_date=check_in,
        end_date=check_out,
        cost=Decimal("250.00"),
        booking_status=BookingStatus.confirmed
    )
    
    await BookingService.create_new_booking(
        db=db_session, 
        booking_data=booking_data, 
        client_id=created_client.id
    )
     # Принудительно отправляем данные в базу и очищаем локальный кеш сессии
    await db_session.flush()
    db_session.expunge_all() 

    # ШАГ 3: Ищем снова на те же даты
    # Твой роутер /search должен отработать overlaps с ApartmentAvailability.is_blocked == True
    response_after = await client.get("/apartments/search", params=search_params)
    assert response_after.status_code == 200
    assert not any(a["id"] == created_apartment.id for a in response_after.json()), "Квартира должна быть скрыта"

    # ШАГ 4: Проверяем другие даты (на март 2026)
    search_params["check_in"] = date(2026, 3, 1).isoformat()
    search_params["check_out"] = date(2026, 3, 5).isoformat()
    
    response_march = await client.get("/apartments/search", params=search_params)
    assert any(a["id"] == created_apartment.id for a in response_march.json()), "На другие даты квартира должна быть видна"
