import asyncio
import uuid
import sys
import os
from sqlalchemy import select

# Добавляем корень проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.landlord import Landlord
from app.models.apartment import Apartment
from app.models.photo import Photo

async def create_seed_data():
    async with AsyncSessionLocal() as db:
        try:
            # Список апартаментов для создания (февраль 2026)
            apartments_to_create = [
                {
                    "name": "Luxury Penthouse St. Petersburg",
                    "address": "456 Sky Tower, Saint Petersburg",
                    "location": "POINT(30.3351 59.9343)",
                    "price": 5500.0,
                    "email": "petersburg_owner@example.com"
                },
                {
                    "name": "Modern Loft Moscow",
                    "address": "12 Tverskaya St, Moscow",
                    "location": "POINT(37.6173 55.7558)",
                    "price": 8500.0,
                    "email": "moscow_owner@example.com"
                },
                {
                    "name": "Cozy Studio Kazan",
                    "address": "5 Bauman St, Kazan",
                    "location": "POINT(49.1064 55.7887)",
                    "price": 3200.0,
                    "email": "kazan_owner@example.com"
                }
            ]

            for item in apartments_to_create:
                # ПРОВЕРКА: Если такой юзер уже есть — пропускаем создание этой группы
                existing_user = await db.execute(select(User).where(User.email == item["email"]))
                if existing_user.scalar_one_or_none():
                    print(f"⚠️ Объект '{item['name']}' уже существует в базе, пропускаем...")
                    continue

                uid = uuid.uuid4().hex[:4]
                
                # 1. Создаем Юзера
                user = User(
                    email=item["email"],
                    phone_number=f"+7{str(uuid.uuid4().int)[:10]}",
                    password_hash="hashed_password_123",
                    telegram_username=f"tg_owner_{uid}"
                )
                db.add(user)
                await db.flush() 

                # 2. Создаем Лендлорда
                landlord = Landlord(
                    user_id=user.id, 
                    first_name="Иван", 
                    last_name=f"Хозяин_{uid}"
                )
                db.add(landlord)
                await db.flush() 

                # 3. Создаем Апартамент
                apartment = Apartment(
                    name=item["name"],
                    description="Premium stay with modern amenities. Data actual for 2026.",
                    price_per_night=item["price"],
                    address=item["address"],
                    location=item["location"],
                    landlord_id=landlord.id,
                )
                db.add(apartment)
                await db.flush()

                # 4. Добавляем фото (используем твой рабочий локальный путь)
                photo = Photo(apartment_id=apartment.id, url="/images/4Gostinaya_1.jpg")
                db.add(photo)

                print(f"✅ Создан: {item['name']} (ID: {apartment.id})")

            await db.commit()
            print("\n🚀 База успешно наполнена актуальными данными!")

        except Exception as e:
            await db.rollback()
            print(f"❌ Ошибка: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(create_seed_data())
