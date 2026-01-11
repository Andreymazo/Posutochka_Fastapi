import asyncio
from datetime import UTC, date, datetime
from decimal import Decimal

from geoalchemy2.elements import WKTElement

# Работа с диапазонами дат PostgreSQL
from psycopg.types.range import Range

# Импорт настроек и движка из вашего database.py
from app.database import AsyncSessionLocal, async_engine

# Импорт моделей
from app.models import Apartment, ApartmentAvailability, Landlord, Photo, User


async def seed_data():
    # Используем вашу фабрику сессий
    async with AsyncSessionLocal() as session:
        try:
            # Начинаем транзакцию
            async with session.begin():
                # 1. Создаем пользователя (User)
                new_user = User(
                    email="landlord_pro@example.com",
                    phone_number="+79991234567",
                    password_hash="hashed_password_here",
                    registration_date=datetime.now(UTC),
                    telegram_username="best_host_2026"
                )
                session.add(new_user)
                # Flush позволяет получить id, не фиксируя транзакцию
                await session.flush()

                # 2. Создаем профиль Арендодателя (Landlord)
                new_landlord = Landlord(
                    user_id=new_user.id,
                    first_name="Алексей",
                    last_name="Смирнов"
                )
                session.add(new_landlord)
                await session.flush()

                # 3. Создаем апартамент
                # Используем WKTElement для создания точки (долгота, широта)
                # Координаты: 37.6173 (долгота), 55.7558 (широта) — Москва
                point_location = WKTElement("POINT(37.6173 55.7558)", srid=4326)
                new_apartment = Apartment(
                    landlord_id=new_landlord.id,
                    name="Люкс-апартаменты в центре",
                    description="Прекрасный вид на город, современный ремонт 2026 года.",
                    price_per_night=Decimal("5000.00"),
                    address="Москва, ул. Тверская, д. 1",
                    location=point_location
                )
                session.add(new_apartment)
                await session.flush()

                # 4. Добавляем Фотографии (Photo)
                photo1 = Photo(
                    apartment_id=new_apartment.id,
                    url="https://example.com/photo1.jpg",
                    is_main=True
                )
                photo2 = Photo(
                    apartment_id=new_apartment.id,
                    url="https://example.com/photo2.jpg",
                    is_main=False
                )
                session.add_all([photo1, photo2])

                # 5. Настраиваем доступность и цены (ApartmentAvailability)
                # Период новогодних праздников с наценкой
                holiday_period = Range(date(2026, 12, 30), date(2027, 1, 5), bounds="[]")
                holiday_rule = ApartmentAvailability(
                    apartment_id=new_apartment.id,
                    blocked_period=holiday_period,
                    reason="Новогодние праздники",
                    is_blocked=False,
                    custom_price=Decimal("12000.00"),
                    min_stay_days=3
                )

                # Период блокировки (ремонт)
                repair_period = Range(date(2026, 11, 10), date(2026, 11, 15), bounds="[]")
                repair_rule = ApartmentAvailability(
                    apartment_id=new_apartment.id,
                    blocked_period=repair_period,
                    reason="Техническое обслуживание",
                    is_blocked=True,
                    custom_price=None,
                    min_stay_days=1
                )

                session.add_all([holiday_rule, repair_rule])

            # После выхода из блока session.begin() произойдет автоматический commit
            print("Данные успешно добавлены (User -> Landlord -> Apartment -> Photos -> Availability)")

        except Exception as e:
            await session.rollback()
            print(f"Ошибка при заполнении данных: {e}")
            raise
        finally:
            await session.close()

if __name__ == "__main__":
    try:
        asyncio.run(seed_data())
    finally:
        # Явное закрытие пула соединений двигателя
        # Для этого нам и нужен импорт async_engine
        asyncio.run(async_engine.dispose())
    # # Запуск асинхронного сида
    # asyncio.run(seed_data())

# import asyncio
# from datetime import date, datetime, UTC
# from decimal import Decimal
# from sqlalchemy.ext.asyncio import create_async_session, AsyncSession, async_sessionmaker
# from sqlalchemy import select
# from psycopg.types.range import Range # Для работы с DATERANGE

# # Импортируйте ваши модели и базу данных здесь
# from app.database import engine, Base
# from app.models import User, Landlord, Apartment, ApartmentAvailability

# async def seed_data():
#     # Настройка сессии (замените URL на ваш)
#     DATABASE_URL = "postgresql://postgres:123456@localhost:5433/posutochka"
#     engine = create_async_session(DATABASE_URL)
#     async_session = async_sessionmaker(engine, expire_on_commit=False)

#     async with async_session() as session:
#         async with session.begin():
#             # 1. Создаем базового пользователя (User)
#             new_user = User(
#                 email="landlord_pro@example.com",
#                 phone_number="+79991234567",
#                 password_hash="hashed_password_here", # В реальном приложении используйте passlib/bcrypt
#                 registration_date=datetime.now(UTC),
#                 telegram_username="best_host_2026"
#             )
#             session.add(new_user)
#             await session.flush() # Получаем ID пользователя

#             # 2. Создаем профиль Арендодателя (Landlord)
#             new_landlord = Landlord(
#                 user_id=new_user.id,
#                 first_name="Алексей",
#                 last_name="Смирнов"
#             )
#             session.add(new_landlord)
#             await session.flush()

#             # 3. Создаем Апартамент (предположим, модель Apartment уже есть)
#             new_apartment = Apartment(
#                 landlord_id=new_landlord.id,
#                 title="Люкс-апартаменты в центре",
#                 base_price=Decimal("5000.00")
#             )
#             session.add(new_apartment)
#             await session.flush()

#             # 4. Создаем настройки календаря (ApartmentAvailability)
#             # Пример: Блокируем даты на ремонт или спец. цену
#             # Range(start, end, bounds='[]') включает обе даты
#             holiday_period = Range(date(2026, 12, 30), date(2027, 1, 5), bounds='[]')

#             availability = ApartmentAvailability(
#                 apartment_id=new_apartment.id,
#                 blocked_period=holiday_period,
#                 reason="Новогодние праздники - повышенный тариф",
#                 is_blocked=False, # Не блокируем совсем, а просто меняем условия
#                 custom_price=Decimal("12000.00"), # Наценка в 2.5 раза
#                 min_stay_days=3 # Минимум 3 ночи в праздники
#             )

#             # Пример блокировки на ремонт (полный запрет бронирования)
#             repair_period = Range(date(2026, 11, 10), date(2026, 11, 15), bounds='[]')
#             repair_block = ApartmentAvailability(
#                 apartment_id=new_apartment.id,
#                 blocked_period=repair_period,
#                 reason="Плановый косметический ремонт",
#                 is_blocked=True, # Бронирование будет запрещено
#                 min_stay_days=1
#             )

#             session.add_all([availability, repair_block])

#         await session.commit()
#         print("Данные успешно добавлены!")

# if __name__ == "__main__":
#     asyncio.run(seed_data())
