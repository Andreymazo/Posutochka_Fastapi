#!/usr/bin/env python
"""Seed script for creating initial user, landlord, and client data.

This script populates the database with sample data for development and testing purposes.
It should be run after applying Alembic migrations.

Usage:
    python scripts/seed_create_user_landlord_client.py

Environment:
    DATABASE_URL: PostgreSQL connection string (optional, defaults to local development settings)
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import Apartment, Client, Landlord, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# def seed_users() -> list[User]:
#     """Create sample users in the database."""
#     users_data: list[dict[str, str | None]] = [
#         {
#             "email": "landlord1@example.com",
#             "phone_number": "+1234567890",
#             "password_hash": "hashed_password_landlord1",
#             "role": "landlord",
#             "telegram_username": "@landlord1",
#             "first_name": "John",       # 👈 Добавили обязательное поле
#             "last_name": "Smith",       # 👈 Добавили обязательное поле
#         },
#         {
#             "email": "landlord2@example.com",
#             "phone_number": "+1234567891",
#             "password_hash": "hashed_password_landlord2",
#             "role": "landlord",
#             "telegram_username": "@landlord2",
#             "first_name": "Maria",      # 👈 Добавили
#             "last_name": "Garcia",      # 👈 Добавили
#         },
#         {
#             "email": "client1@example.com",
#             "phone_number": "+1234567892",
#             "password_hash": "hashed_password_client1",
#             "role": "client",
#             "telegram_username": "@client1",
#             "first_name": "Alice",      # 👈 Добавили
#             "last_name": "Johnson",      # 👈 Добавили
#         },
#         {
#             "email": "client2@example.com",
#             "phone_number": "+1234567893",
#             "password_hash": "hashed_password_client2",
#             "role": "client",
#             "telegram_username": None,
#             "first_name": "Bob",        # 👈 Добавили
#             "last_name": "Williams",    # 👈 Добавили
#         },
#     ]

#     users = []
#     for data in users_data:
#         user = User(
#             email=data["email"],
#             phone_number=data["phone_number"],
#             password_hash=data["password_hash"],
#             telegram_username=data["telegram_username"],
#             first_name=data["first_name"], # 👈 Передаем в модель
#             last_name=data["last_name"],   # 👈 Передаем в модель
#         )
#         users.append(user)
#     return users



# def seed_landlords(users: list[User]) -> list[Landlord]:
#     """Create sample landlords linked to users with 'landlord' role."""
#     landlords_data = [
#         {"first_name": "John", "last_name": "Smith"},
#         {"first_name": "Maria", "last_name": "Garcia"},
#     ]

#     landlords = []
#     landlord_users = [u for u in users if u.role == "landlord"]

#     for user, data in zip(landlord_users, landlords_data, strict=False):
#         landlord = Landlord(
#             user_id=user.id,
#             first_name=data["first_name"],
#             last_name=data["last_name"],
#         )
#         landlords.append(landlord)
#     return landlords


# def seed_clients(users: list[User]) -> list[Client]:
#     """Create sample clients linked to users with 'client' role."""
#     clients_data = [
#         {"first_name": "Alice", "last_name": "Johnson"},
#         {"first_name": "Bob", "last_name": "Williams"},
#     ]

#     clients = []
#     client_users = [u for u in users if u.role == "client"]

#     for user, data in zip(client_users, clients_data, strict=False):
#         client = Client(
#             user_id=user.id,
#             first_name=data["first_name"],
#             last_name=data["last_name"],
#         )
#         clients.append(client)
#     return clients


def seed_apartments() -> list[Apartment]:
    """Create sample apartments in the database."""
    apartments_data = [
        {
            "name": "Cozy Studio Downtown",
            "description": "A beautiful studio apartment in the heart of the city center. "
            "Perfect for couples or solo travelers.",
            "price_per_night": 75.00,
            "address": "123 Main Street, Downtown",
        },
        {
            "name": "Spacious 2BR Near Park",
            "description": "Spacious two-bedroom apartment with stunning park views. "
            "Ideal for families or groups.",
            "price_per_night": 120.00,
            "address": "456 Park Avenue, Green District",
        },
        {
            "name": "Modern Loft",
            "description": "Stylish modern loft with exposed brick walls and high ceilings.",
            "price_per_night": 95.00,
            "address": "789 Industrial Way, Arts Quarter",
        },
    ]

    apartments = []
    for data in apartments_data:
        apartment = Apartment(
            name=data["name"],
            description=data["description"],
            price_per_night=data["price_per_night"],
            address=data["address"],
        )
        apartments.append(apartment)
    return apartments


import asyncio
from sqlalchemy import select, func
async def run_seed() -> None:
    """Run the database seeding process."""
    logger.info("Starting database seed process...")

    async with SessionLocal() as db:
        try:
            # 1. Проверка наличия данных
            result = await db.execute(select(func.count()).select_from(User))
            existing_users = result.scalar()
            if existing_users > 0:
                logger.warning("База данных уже содержит пользователей. Пропускаем.")
                return

            # Исходные данные со строго прописанными ролями
            users_source_data = [
                {"email": "landlord1@example.com", "role": "landlord", "first_name": "John", "last_name": "Smith"},
                {"email": "landlord2@example.com", "role": "landlord", "first_name": "Maria", "last_name": "Garcia"},
                {"email": "client1@example.com", "role": "client", "first_name": "Alice", "last_name": "Johnson"},
                {"email": "client2@example.com", "role": "client", "first_name": "Bob", "last_name": "Williams"},
            ]

            logger.info("Создаем пользователей...")
            
            # Списки, куда мы разложим созданные объекты SQLAlchemy
            landlord_users = []
            client_users = []

            for data in users_source_data:
                # Создаем пользователя для БД (без поля role!)
                user = User(
                    email=data["email"],
                    phone_number=f"+123456789{users_source_data.index(data)}",
                    password_hash=f"hashed_password_{data['role']}",
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                )
                db.add(user)
                
                # Запоминаем объект в нужный список прямо в памяти скрипта
                if data["role"] == "landlord":
                    landlord_users.append((user, data))
                else:
                    client_users.append((user, data))

            # Сохраняем пользователей в базу, чтобы получить их ID
            await db.commit()
            
            # Нам нужно обновить объекты, чтобы подтянулись сгенерированные id
            for user, _ in landlord_users + client_users:
                await db.refresh(user)

            # 2. Создаем профили лендлордов
            logger.info("Создаем профили арендодателей...")
            landlords_created = 0
            for user, data in landlord_users:
                landlord = Landlord(
                    user_id=user.id,
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                )
                db.add(landlord)
                landlords_created += 1

            # 3. Создаем профили клиентов
            logger.info("Создаем профили клиентов...")
            clients_created = 0
            for user, data in client_users:
                client = Client(
                    user_id=user.id,
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                )
                db.add(client)
                clients_created += 1

            # 4. Создаем квартиры
            logger.info("Создаем квартиры...")
            apartments = seed_apartments()
            db.add_all(apartments)
            
            await db.commit()

            logger.info("База данных успешно наполнена!")
            logger.info(f"Создано пользователей: {len(users_source_data)}")
            logger.info(f"Создано профилей арендодателей: {landlords_created}")
            logger.info(f"Создано профилей клиентов: {clients_created}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка при наполнении базы: {e}")
            raise



if __name__ == "__main__":
    # Запускаем асинхронную функцию через asyncio
    asyncio.run(run_seed())
