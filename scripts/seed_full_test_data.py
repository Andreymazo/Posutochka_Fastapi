import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from geoalchemy2.elements import WKTElement
from psycopg.types.range import Range
from sqlalchemy import select
from app.database import AsyncSessionLocal, async_engine
from app.models import Apartment, ApartmentAvailability, Landlord, Photo, User, Booking, Message,  Client

async def seed_data():
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                
                # 1. Проверяем, есть ли уже такой пользователь
                result = await session.execute(
                    select(User).where(User.email == "landlord_pro@example.com")
                )
                new_user = result.scalar_one_or_none()

                if not new_user:
                    # Если нет — создаем
                    new_user = User(
                        email="landlord_pro@example.com",
                        phone_number="+79991234567",
                        password_hash="hashed_password_here",
                        registration_date=datetime.now(UTC),
                        telegram_username="AndreyMazo",
                        telegram_id=5015736552  # Ваш ID
                    )
                    session.add(new_user)
                else:
                    # Если есть — обновляем его Telegram ID
                    new_user.telegram_id = 5015736552
                    new_user.telegram_username = "AndreyMazo"

                await session.flush()

                  # 2. Создаем или получаем профиль Арендодателя
                landlord_res = await session.execute(select(Landlord).where(Landlord.user_id == new_user.id))
                new_landlord = landlord_res.scalar_one_or_none()
                if not new_landlord:
                    new_landlord = Landlord(user_id=new_user.id, first_name="Алексей", last_name="Смирнов")
                    session.add(new_landlord)
                await session.flush()

                # 3. Создаем апартамент (тут можно просто создавать новый или тоже проверять)
                point_location = WKTElement("POINT(37.6173 55.7558)", srid=4326)
                new_apartment = Apartment(
                    landlord_id=new_landlord.id,
                    name="Люкс-апартаменты в центре",
                    description="Прекрасный вид, ремонт 2026 года.",
                    price_per_night=Decimal("5000.00"),
                    address="Москва, ул. Тверская, д. 1",
                    location=point_location
                )
                session.add(new_apartment)
                await session.flush()

                # 3.1 Создаем или получаем профиль Клиента
                client_res = await session.execute(select(Client).where(Client.user_id == new_user.id))
                new_client = client_res.scalar_one_or_none()
                if not new_client:
                    new_client = Client(user_id=new_user.id, first_name="Иван", last_name="Тестовый")
                    session.add(new_client)
                await session.flush()
                
                # 4. СОЗДАЕМ БРОНИРОВАНИЕ (Нужно для внешней связи Message)
                # Бронь на февраль 2026
                booking_period = Range(date(2026, 2, 10), date(2026, 2, 15), bounds="[]")
                new_booking = Booking(
                    apartment_id=new_apartment.id,
                    landlord_id=new_landlord.id,  # <--- ОБЯЗАТЕЛЬНО ДОБАВИТЬ ЭТО
                    client_id=new_client.id,       # Для теста арендодатель сам у себя клиент
                    booking_period=booking_period,
                    booking_status="confirmed",    # Правильное имя колонки из вашего лога
                    cost=Decimal("25000.00")      # Правильное имя колонки из вашего лога
                )
                session.add(new_booking)
                await session.flush()

                # 5. СОЗДАЕМ СООБЩЕНИЕ-ЗАГЛУШКУ (На него вы будете отвечать Reply)
                # !!! ЗАМЕНИТЕ 100 на message_id из консоли вашего бота !!!
                TEST_MESSAGE_ID = 30 
                
                fake_message = Message(
                    text="Вопрос от клиента: 'Есть ли у вас Wi-Fi?'",
                    booking_id=new_booking.id,
                    sender_id=new_user.id,
                    tg_message_id=TEST_MESSAGE_ID, # Код в chat.py будет искать по этому полю
                    is_read=True
                )
                session.add(fake_message)

            print("✅ База заполнена! Создан User, Landlord, Apartment, Booking и тестовое Message.")
            print(f"👉 Сделайте Reply на сообщение с ID {TEST_MESSAGE_ID} в Telegram.")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            raise
        finally:
            await session.close()

if __name__ == "__main__":
    try:
        asyncio.run(seed_data())
    finally:
        asyncio.run(async_engine.dispose())
