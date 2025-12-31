"""Seed script to create a booking with multiple payments.

Demonstrates one-to-many relationship: one Booking has multiple Payments.
Run with: python -m seed_create_booking_with_payments
"""

from datetime import UTC, datetime, timedelta

from app.database import SessionLocal
from app.models.apartment import Apartment
from app.models.booking import Booking
from app.models.client import Client
from app.models.landlord import Landlord
from app.models.payment import Payment
from app.models.user import User


def create_booking_with_payments() -> None:
    """Create a booking with two payments to demonstrate one-to-many relationship."""
    db = SessionLocal()

    try:
        # Create user for client
        user_client_data = {
            "email": "client_booking@example.com",
            "phone_number": "+1111111111",
            "password_hash": "hashed_password_client_booking",
        }
        db_user_client = User(**user_client_data)
        db.add(db_user_client)
        db.commit()
        print(f"Created user for client: id={db_user_client.id}")

        # Create client
        client_data = {
            "user_id": db_user_client.id,
            "first_name": "Ivan",
            "last_name": "Petrov",
        }
        db_client = Client(**client_data)
        db.add(db_client)
        db.commit()
        print(f"Created client: id={db_client.id}")

        # Create user for landlord
        user_landlord_data = {
            "email": "landlord_booking@example.com",
            "phone_number": "+2222222222",
            "password_hash": "hashed_password_landlord_booking",
        }
        db_user_landlord = User(**user_landlord_data)
        db.add(db_user_landlord)
        db.commit()
        print(f"Created user for landlord: id={db_user_landlord.id}")

        # Create landlord
        landlord_data = {
            "user_id": db_user_landlord.id,
            "first_name": "Sergei",
            "last_name": "Sidorov",
        }
        db_landlord = Landlord(**landlord_data)
        db.add(db_landlord)
        db.commit()
        print(f"Created landlord: id={db_landlord.id}")

        # Create apartment
        apartment_data = {
            "name": "Cozy Studio",
            "description": "A cozy studio apartment in the city center",
            "price_per_night": 50.0,
            "address": "123 Main Street, Moscow",
            "location": "POINT(37.6173 55.7558)",  # Moscow coordinates (lon, lat)
        }
        db_apartment = Apartment(**apartment_data)
        db.add(db_apartment)
        db.commit()
        print(f"Created apartment: id={db_apartment.id}")

        # Create booking
        start_date = datetime.now(UTC) + timedelta(days=7)
        end_date = start_date + timedelta(days=5)
        total_cost = 5 * apartment_data["price_per_night"]  # 5 nights

        booking_data = {
            "start_date": start_date,
            "end_date": end_date,
            "cost": total_cost,
            "booking_status": "confirmed",
            "landlord_id": db_landlord.id,
            "client_id": db_client.id,
            "apartment_id": db_apartment.id,
        }
        db_booking = Booking(**booking_data)
        db.add(db_booking)
        db.commit()
        print(f"Created booking: id={db_booking.id}, cost={db_booking.cost}")

        # Create first payment (partial payment - deposit)
        payment1_data = {
            "booking_id": db_booking.id,
            "amount": total_cost * 0.3,  # 30% deposit
            "payment_status": "paid",
        }
        db_payment1 = Payment(**payment1_data)
        db.add(db_payment1)
        db.commit()
        print(f"Created payment 1 (deposit): id={db_payment1.id}, amount={db_payment1.amount}")

        # Create second payment (remaining balance)
        payment2_data = {
            "booking_id": db_booking.id,
            "amount": total_cost * 0.7,  # 70% remaining
            "payment_status": "pending",
        }
        db_payment2 = Payment(**payment2_data)
        db.add(db_payment2)
        db.commit()
        print(f"Created payment 2 (balance): id={db_payment2.id}, amount={db_payment2.amount}")

        # Verify one-to-many relationship
        db.refresh(db_booking)
        print("\nVerifying relationship:")
        print(f"Booking {db_booking.id} has {len(db_booking.payments)} payment(s):")
        for payment in db_booking.payments:
            print(
                f"  - Payment {payment.id}: amount={payment.amount}, status={payment.payment_status}"
            )

        print("\nSeed data created successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error creating seed data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_booking_with_payments()
