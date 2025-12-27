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


def seed_users() -> list[User]:
    """Create sample users in the database."""
    users_data: list[dict[str, str | None]] = [
        {
            "email": "landlord1@example.com",
            "phone_number": "+1234567890",
            "password_hash": "hashed_password_landlord1",  # In production, use proper hashing
            "role": "landlord",
            "telegram_username": "@landlord1",
        },
        {
            "email": "landlord2@example.com",
            "phone_number": "+1234567891",
            "password_hash": "hashed_password_landlord2",
            "role": "landlord",
            "telegram_username": "@landlord2",
        },
        {
            "email": "client1@example.com",
            "phone_number": "+1234567892",
            "password_hash": "hashed_password_client1",
            "role": "client",
            "telegram_username": "@client1",
        },
        {
            "email": "client2@example.com",
            "phone_number": "+1234567893",
            "password_hash": "hashed_password_client2",
            "role": "client",
            "telegram_username": None,
        },
    ]

    users = []
    for data in users_data:
        user = User(
            email=data["email"],
            phone_number=data["phone_number"],
            password_hash=data["password_hash"],
            role=data["role"],
            telegram_username=data["telegram_username"],
        )
        users.append(user)
    return users


def seed_landlords(users: list[User]) -> list[Landlord]:
    """Create sample landlords linked to users with 'landlord' role."""
    landlords_data = [
        {"first_name": "John", "last_name": "Smith"},
        {"first_name": "Maria", "last_name": "Garcia"},
    ]

    landlords = []
    landlord_users = [u for u in users if u.role == "landlord"]

    for user, data in zip(landlord_users, landlords_data, strict=False):
        landlord = Landlord(
            user_id=user.id,
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        landlords.append(landlord)
    return landlords


def seed_clients(users: list[User]) -> list[Client]:
    """Create sample clients linked to users with 'client' role."""
    clients_data = [
        {"first_name": "Alice", "last_name": "Johnson"},
        {"first_name": "Bob", "last_name": "Williams"},
    ]

    clients = []
    client_users = [u for u in users if u.role == "client"]

    for user, data in zip(client_users, clients_data, strict=False):
        client = Client(
            user_id=user.id,
            first_name=data["first_name"],
            last_name=data["last_name"],
        )
        clients.append(client)
    return clients


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


def run_seed() -> None:
    """Run the database seeding process."""
    logger.info("Starting database seed process...")

    db = SessionLocal()
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            logger.warning(
                f"Database already contains {existing_users} users. "
                "Skipping seed to avoid duplicates."
            )
            logger.info("To re-seed, please clear the existing data first.")
            return

        # Create users
        logger.info("Creating users...")
        users = seed_users()
        for user in users:
            db.add(user)
        db.commit()

        # Refresh users to get their IDs
        for user in users:
            db.refresh(user)
        logger.info(f"Created {len(users)} users")

        # Create landlords
        logger.info("Creating landlords...")
        landlords = seed_landlords(users)
        for landlord in landlords:
            db.add(landlord)
        db.commit()
        logger.info(f"Created {len(landlords)} landlords")

        # Create clients
        logger.info("Creating clients...")
        clients = seed_clients(users)
        for client in clients:
            db.add(client)
        db.commit()
        logger.info(f"Created {len(clients)} clients")

        # Create apartments
        logger.info("Creating apartments...")
        apartments = seed_apartments()
        for apartment in apartments:
            db.add(apartment)
        db.commit()
        logger.info(f"Created {len(apartments)} apartments")

        logger.info("Database seed completed successfully!")

        # Print summary
        logger.info("\n" + "=" * 50)
        logger.info("SEED SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Users created: {len(users)}")
        logger.info(f"  - Landlords: {len([u for u in users if u.role == 'landlord'])}")
        logger.info(f"  - Clients: {len([u for u in users if u.role == 'client'])}")
        logger.info(f"Landlord profiles: {len(landlords)}")
        logger.info(f"Client profiles: {len(clients)}")
        logger.info(f"Apartments: {len(apartments)}")
        logger.info("=" * 50)

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {e}")
        logger.error("This may occur if data with duplicate unique fields already exists.")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
