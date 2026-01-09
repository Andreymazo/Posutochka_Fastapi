import asyncio
from datetime import date
from decimal import Decimal
from psycopg.types.range import Range
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Booking, Client, User, Landlord, Apartment

async def ensure_apartment_exists(session):
    """Проверяет наличие апартамента с ID=3, если нет — создает всю цепочку."""
    # 1. Проверяем апартамент
    result = await session.execute(select(Apartment).filter_by(id=3))
    apt = result.scalar_one_or_none()
    
    if apt:
        return apt.landlord_id

    # 2. Если нет, создаем Арендодателя (User + Landlord)
    ts = int(asyncio.get_event_loop().time())
    owner_user = User(
        email=f"owner_{ts}@example.com",
        phone_number=f"+7111{ts % 1000000:06d}",
        password_hash="hash"
    )
    session.add(owner_user)
    await session.flush()

    landlord = Landlord(user_id=owner_user.id, first_name="Хозяин", last_name="Тестовый")
    session.add(landlord)
    await session.flush()

    # 3. Создаем Апартамент с принудительным ID=3 (если это позволяет sequence)
    # Или просто используем тот ID, который выдаст база
    new_apt = Apartment(
        id=3, # Пробуем задать ID явно для соответствия вашему запросу
        name="Тестовый апартамент",
        price_per_night=Decimal("5000.00"),
        address="Тестовый адрес",
        landlord_id=landlord.id,
        location="POINT(37.6173 55.7558)" # Москва
    )
    session.add(new_apt)
    await session.flush()
    return landlord.id

async def test_overbooking_logic():
    async with AsyncSessionLocal() as session:
        try:
            # --- ПОДГОТОВКА ---
            landlord_id = await ensure_apartment_exists(session)

            # Создаем уникального Клиента (User + Client)
            ts = int(asyncio.get_event_loop().time())
            test_user = User(
                email=f"guest_{ts}@example.com",
                phone_number=f"+7999{ts % 1000000:06d}",
                password_hash="hash"
            )
            session.add(test_user)
            await session.flush()

            test_client = Client(user_id=test_user.id, first_name="Гость", last_name="Тестовый")
            session.add(test_client)
            await session.flush()

            # --- САМ ТЕСТ ---
            # 1. Создаем ПЕРВУЮ бронь (успешную)
            booking1 = Booking(
                apartment_id=3,
                landlord_id=landlord_id,
                client_id=test_client.id,
                booking_period=Range(date(2026, 6, 1), date(2026, 6, 10), bounds='[]'),
                cost=Decimal("45000.00"),
                booking_status="confirmed"
            )
            session.add(booking1)
            await session.commit() # Фиксируем первую бронь
            print("Первая бронь создана успешно.")

            # 2. Пытаемся создать ВТОРУЮ бронь на те же даты
            async with AsyncSessionLocal() as session2: # Новая сессия для чистоты эксперимента
                conflict_booking = Booking(
                    apartment_id=3,
                    landlord_id=landlord_id,
                    client_id=test_client.id,
                    booking_period=Range(date(2026, 6, 5), date(2026, 6, 15), bounds='[]'),
                    cost=Decimal("50000.00"),
                    booking_status="confirmed"
                )
                session2.add(conflict_booking)
                
                try:
                    await session2.commit()
                    print("ОШИБКА: База пропустила овербукинг!")
                except Exception as e:
                    await session2.rollback()
                    if "conflicts with existing key" in str(e) or "exclude" in str(e).lower():
                        print("ПОБЕДА: Индекс GIST заблокировал пересечение дат!")
                    else:
                        print(f"ДРУГАЯ ОШИБКА БД: {e}")

        except Exception as e:
            await session.rollback()
            print(f"ОШИБКА ПОДГОТОВКИ ТЕСТА: {e}")

if __name__ == "__main__":
    asyncio.run(test_overbooking_logic())

# Теперь, когда фундамент (модели и база) непоколебим, пора переходить к бизнес-логике и API.
# Я рекомендую следующий план:
# 1. Сервис расчета стоимости (Pricing Service)
# Нужно написать функцию, которая:

#     Принимает apartment_id и даты.
#     Ищет ApartmentAvailability для этих дат.
#     Считает сумму: (количество ночей с базовой ценой) + (ночи с custom_price).
#     Проверяет min_stay_days.

# 2. Поиск по гео-локации (Spatial Search)
# Реализовать эндпоинт GET /apartments/search, который принимает широту, долготу и радиус (в метрах) и возвращает ближайшие апартаменты. Благодаря PostGIS, запрос в SQLAlchemy будет выглядеть примерно так:
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