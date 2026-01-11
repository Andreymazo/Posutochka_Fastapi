import pytest
from datetime import date
from decimal import Decimal
from psycopg.types.range import Range
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Booking

@pytest.mark.asyncio
async def test_overbooking_logic(
    db_session: AsyncSession,
    created_client: any,
    created_apartment: any,
    created_landlord: any
):
    """
    Тест проверяет, что база данных (GIST индекс) блокирует пересекающиеся даты.
    """
    # 1. Создаем ПЕРВУЮ бронь (успешную)
    # Используем созданные фикстурами объекты для корректности связей
    booking1 = Booking(
        apartment_id=created_apartment.id,
        landlord_id=created_landlord.id,
        client_id=created_client.id,
        booking_period=Range(date(2026, 6, 1), date(2026, 6, 10), bounds='[]'),
        cost=Decimal("45000.00"),
        booking_status="confirmed"
    )
    db_session.add(booking1)
    await db_session.commit()

    # 2. Пытаемся создать ВТОРУЮ бронь на те же даты в НОВОЙ транзакции
    # Мы используем новую транзакцию, так как предыдущая завершена commit-ом
    conflict_booking = Booking(
        apartment_id=created_apartment.id,
        landlord_id=created_landlord.id,
        client_id=created_client.id,
        booking_period=Range(date(2026, 6, 5), date(2026, 6, 15), bounds='[]'),
        cost=Decimal("50000.00"),
        booking_status="confirmed"
    )
    db_session.add(conflict_booking)
    
    # Ожидаем исключение от БД (ExclusionConstraint)
    with pytest.raises(Exception) as excinfo:
        await db_session.commit()
    
    # Проверяем, что ошибка именно от индекса пересечений (GIST)
    assert "exclude" in str(excinfo.value).lower() or "conflicts with existing key" in str(excinfo.value).lower()
    
    await db_session.rollback()

# Теперь, когда фундамент (модели и база) непоколебим, пора переходить к бизнес-логике и API.
# Я рекомендую следующий план:
# 1. Сервис расчета стоимости (Pricing Service)
# Нужно написать функцию, которая:

#     Принимает apartment_id и даты.
#     Ищет ApartmentAvailability для этих дат.
#     Считает сумму: (количество ночей с базовой ценой) + (ночи с custom_price).
#     Проверяет min_stay_days.

# 2. Поиск по гео-локации (Spatial Search)
# Реализовать эндпоинт GET /apartments/search, который принимает широту, долготу и радиус 
# (в метрах) и возвращает ближайшие апартаменты. Благодаря PostGIS, запрос в SQLAlchemy будет 
# выглядеть примерно так:
# python

# from geoalchemy2.functions import ST_DWithin
# # ...
# stmt = select(Apartment).where(ST_DWithin(Apartment.location, point, radius))

# Используйте код с осторожностью.
# 3. Эндпоинт создания бронирования
# POST /bookings, который:

#     Валидирует данные.
#     Вызывает расчет стоимости.
#     Создает запись в Booking.
#     (В будущем) Создает транзакцию в WalletTransaction и обновляет Balance.

# С чего начнем? Можем набросать логику расчета цены или первый гео-эндпоинт на FastAPI.