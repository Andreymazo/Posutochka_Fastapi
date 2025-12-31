"""Seed script to create initial user, landlord, and client data.

Demonstrates the relationship between User, Client, and Landlord models.
Run with: python -m seed_create_user_landlord_client
"""

from app.database import SessionLocal
from app.models.client import Client
from app.models.landlord import Landlord
from app.models.user import User


def create_initial_data() -> None:
    """Create initial users, client, and landlord records."""
    db = SessionLocal()

    try:
        # Create user1 (will be a client)
        user1_data = {
            "email": "user@example.com",
            "phone_number": "+1234567890",
            "password_hash": "hashed_password_user",
        }
        db_user1 = User(**user1_data)
        db.add(db_user1)
        db.commit()

        # Create client linked to user1
        print(f"Created user1 with id={db_user1.id}")
        client_data = {
            "first_name": "Jane",
            "last_name": "Smith",
        }
        db_client = Client(**client_data, user_id=db_user1.id)
        db.add(db_client)
        db.commit()
        print(f"Created client with id={db_client.id}")

        # Create user2 (will be a landlord)
        user2_data = {
            "email": "user2@existing.pay",
            "phone_number": "+1230987563",
            "password_hash": "hashed_password_user2",
        }
        db_user2 = User(**user2_data)
        db.add(db_user2)
        db.commit()

        # Create landlord linked to user2
        print(f"Created user2 with id={db_user2.id}")
        landlord_data = {
            "first_name": "John2",
            "last_name": "Doe2",
        }
        db_landlord = Landlord(**landlord_data, user_id=db_user2.id)
        db.add(db_landlord)
        db.commit()
        print(f"Created landlord with id={db_landlord.id}")

        print("\nSeed data created successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error creating seed data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_initial_data()
