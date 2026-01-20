import asyncio
from datetime import UTC, date, datetime
from decimal import Decimal
from geoalchemy2.elements import WKTElement
from psycopg.types.range import Range
from sqlalchemy import select
from app.database import AsyncSessionLocal, async_engine
from app.models import Apartment, Landlord, User, Booking, Message, Client

async def get_or_create_user(session, email, phone, tg_id, username, first_name):
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            phone_number=phone,
            password_hash="test_hash_2026",
            registration_date=datetime.now(UTC),
            telegram_username=username,
            telegram_id=tg_id
        )
        session.add(user)
        await session.flush()
    else:
        user.telegram_id = tg_id
        user.telegram_username = username
    
    # Landlord
    res_l = await session.execute(select(Landlord).where(Landlord.user_id == user.id))
    landlord = res_l.scalar_one_or_none()
    if not landlord:
        landlord = Landlord(user_id=user.id, first_name=first_name, last_name="Тестовый")
        session.add(landlord)
    
    # Client
    res_c = await session.execute(select(Client).where(Client.user_id == user.id))
    client = res_c.scalar_one_or_none()
    if not client:
        client = Client(user_id=user.id, first_name=first_name, last_name="Клиент")
        session.add(client)
    
    await session.flush()
    return user, landlord, client

async def seed_data():
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                # 1. Получаем/создаем пользователей Андрея и Охунжона
                andrey_u, andrey_l, andrey_c = await get_or_create_user(
                    session, "andrey@mazo.ru", "+7999111", 5015736552, "AndreyMazo", "Андрей"
                )
                oxun_u, oxun_l, oxun_c = await get_or_create_user(
                    session, "oxunjon@test.uz", "+7999222", 337067936, "Oxunjon", "Охунжон"
                )

                # 2. Создаем апартаменты (ТЕПЕРЬ С АДРЕСАМИ)
                apt_andrey = Apartment(
                    landlord_id=andrey_l.id,
                    name="Студия Андрея в Москве",
                    address="Москва, ул. Ленина, 10", # Исправлено: адрес добавлен
                    price_per_night=Decimal("4000.00"),
                    location=WKTElement("POINT(37.6 55.7)", srid=4326)
                )
                apt_oxun = Apartment(
                    landlord_id=oxun_l.id,
                    name="Пентхаус Охунжона",
                    address="Ташкент, пр-т Навои, 1", # Исправлено: адрес добавлен
                    price_per_night=Decimal("7000.00"),
                    location=WKTElement("POINT(37.7 55.8)", srid=4326)
                )
                session.add_all([apt_andrey, apt_oxun])
                await session.flush()

                # 3. Бронирование 1: Охунжон у Андрея
                b1 = Booking(
                    apartment_id=apt_andrey.id,
                    landlord_id=andrey_l.id,
                    client_id=oxun_c.id,
                    booking_period=Range(date(2026, 3, 1), date(2026, 3, 5), bounds="[]"),
                    booking_status="pending",
                    cost=Decimal("16000.00")
                )
                # 4. Бронирование 2: Андрей у Охунжона
                b2 = Booking(
                    apartment_id=apt_oxun.id,
                    landlord_id=oxun_l.id,
                    client_id=andrey_c.id,
                    booking_period=Range(date(2026, 4, 10), date(2026, 4, 15), bounds="[]"),
                    booking_status="pending",
                    cost=Decimal("35000.00")
                )
                session.add_all([b1, b2])
                await session.flush()

                # 5. Сообщения для Reply (связываем с реальными message_id из ваших чатов)
                m1 = Message(
                    text="Бронирование у Андрея. Подтвердите ответом на это сообщение.",
                    booking_id=b1.id,
                    sender_id=andrey_u.id,
                    tg_message_id=39,
                    is_read=False
                )
                m2 = Message(
                    text="Бронирование у Охунжона. Подтвердите ответом на это сообщение.",
                    booking_id=b2.id,
                    sender_id=oxun_u.id,
                    tg_message_id=40,
                    is_read=False
                )
                session.add_all([m1, m2])

            print("\n✅ [SUCCESS] Сценарий загружен.")
            print(f"Андрей (ID 5015736552) -> сделай Reply на сообщение с ID 39")
            print(f"Охунжон (ID 337067936) -> сделай Reply на сообщение с ID 40")

        except Exception as e:
            print(f"❌ Ошибка IntegrityError исправлена добавлением адреса: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_data())
