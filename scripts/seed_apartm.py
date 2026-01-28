import asyncio
import uuid
import sys
import os
import aioboto3
import random
from sqlalchemy import select
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.landlord import Landlord
from app.models.apartment import Apartment
from app.models.photo import Photo

MINIO_SETTINGS = {
    "endpoint_url": "http://minio:9000",
    "access_key": "admin",
    "secret_key": "strong_password_2026",
    "bucket_name": "apartments",
}

# Координаты центра Питера
SPB_CENTER = {"lat": 59.9343, "lon": 30.3351}

async def upload_photo_to_minio(file_path: str, object_name: str):
    session = aioboto3.Session()
    async with session.client(
        's3',
        endpoint_url=MINIO_SETTINGS["endpoint_url"],
        aws_access_key_id=MINIO_SETTINGS["access_key"],
        aws_secret_access_key=MINIO_SETTINGS["secret_key"]
    ) as s3:
        # 1. Авто-создание бакета, если его нет
        try:
            await s3.head_bucket(Bucket=MINIO_SETTINGS["bucket_name"])
        except:
            print(f"📦 Создаю бакет {MINIO_SETTINGS['bucket_name']}...")
            await s3.create_bucket(Bucket=MINIO_SETTINGS["bucket_name"])
            
            # 2. Делаем бакет ПУБЛИЧНЫМ (Anonymous Download)
            import json
            policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{MINIO_SETTINGS['bucket_name']}/*"]
                }]
            }
            await s3.put_bucket_policy(Bucket=MINIO_SETTINGS["bucket_name"], Policy=json.dumps(policy))

        # 3. Сама загрузка файла
        with open(file_path, "rb") as file_data:
            await s3.put_object(
                Bucket=MINIO_SETTINGS["bucket_name"],
                Key=object_name,
                Body=file_data,
                ContentType="image/jpeg"
            )
    return f"/{MINIO_SETTINGS['bucket_name']}/{object_name}"

# async def upload_photo_to_minio(file_path: str, object_name: str):
#     session = aioboto3.Session()
#     async with session.client('s3', endpoint_url=MINIO_SETTINGS["endpoint_url"],
#                               aws_access_key_id=MINIO_SETTINGS["access_key"],
#                               aws_secret_access_key=MINIO_SETTINGS["secret_key"]) as s3:
#         with open(file_path, "rb") as file_data:
#             await s3.put_object(Bucket=MINIO_SETTINGS["bucket_name"], Key=object_name,
#                                 Body=file_data, ContentType="image/jpeg")
#     return f"/{MINIO_SETTINGS['bucket_name']}/{object_name}"

async def create_massive_seed():
    media_path = "/app/media/apartments"
    available_photos = ["pic2.jpg", "pic3.jpg", "pic4.jpg", "pic5.jpg", "pic6.jpg", "pic7house.jpg"]
    
    async with AsyncSessionLocal() as db:
        print(f"🏘️ Начинаем заселение Питера (2026)...")
        
        for i in range(50):
            try:
                # Генерируем небольшое смещение от центра (примерно до 15 км)
                lat = SPB_CENTER["lat"] + random.uniform(-0.1, 0.1)
                lon = SPB_CENTER["lon"] + random.uniform(-0.15, 0.15)
                
                uid = uuid.uuid4().hex[:6]
                email = f"owner_{uid}@spb.ru"
                
                # 1. Юзер
                user = User(
                    first_name=random.choice(["Иван", "Сергей", "Анна", "Мария", "Петр"]),
                    last_name=f"Питерский_{i}",
                    email=email,
                    phone_number=f"+7999{random.randint(1000000, 9999999)}",
                    password_hash="hash",
                    telegram_id=random.randint(100000000, 999999999),
                    is_email_verified=True
                )
                db.add(user)
                await db.flush()

                # 2. Лендлорд
                landlord = Landlord(user_id=user.id)
                db.add(landlord)
                await db.flush()

                # 3. Апартамент
                price = random.randrange(2500, 15000, 100)
                apt = Apartment(
                    name=f"Уютная студия #{i+1}",
                    description="Отличный вариант для проживания в 2026 году. Вид на город.",
                    price_per_night=float(price),
                    address=f"Спб, ул. Примерная, д. {i+1}",
                    location=f"POINT({lon} {lat})", # ВАЖНО: В PostGIS сначала Longitude, потом Latitude
                    landlord_id=landlord.id
                )
                db.add(apt)
                await db.flush()

                # 4. Фото (выбираем одно из 6 имеющихся)
                chosen_img = random.choice(available_photos)
                local_img_path = os.path.join(media_path, chosen_img)
                
                if os.path.exists(local_img_path):
                    # Чтобы не плодить дубликаты в MinIO, можно использовать имя файла как ключ
                    # Но для сидов с UUID надежнее
                    minio_name = f"seed_{uid}_{chosen_img}"
                    minio_url = await upload_photo_to_minio(local_img_path, minio_name)
                    
                    photo = Photo(apartment_id=apt.id, url=minio_url)
                    db.add(photo)
                
                if i % 10 == 0:
                    print(f"✅ Создано {i} объектов...")

            except Exception as e:
                print(f"❌ Ошибка на шаге {i}: {e}")
                continue

        await db.commit()
        print(f"\n🚀 Готово! 50 объектов в Питере ждут тебя на карте.")

if __name__ == "__main__":
    asyncio.run(create_massive_seed())
