"""Seed script to create User, Landlord, Apartment, and Photos with proper relationships.

Demonstrates the complete OTM (One-To-Many) relationships:
- One User has One Landlord (One-to-One via unique user_id)
- One Landlord has Many Apartments (One-to-Many)
- One Apartment has Many Photos (One-to-Many)

Run with: python -m seed_create_user_landlord_apartment_with_photos
"""

from app.database import SessionLocal
from app.models.apartment import Apartment
from app.models.landlord import Landlord
from app.models.photo import Photo
from app.models.user import User


def create_complete_data() -> None:
    """Create User, Landlord, Apartments with Photos to demonstrate all relationships."""
    db = SessionLocal()

    try:
        # Step 1: Create User
        print("Step 1: Creating User...")
        user_data = {
            "email": "landlord@example.com",
            "phone_number": "+1234567890",
            "password_hash": "hashed_password_123",
            "telegram_username": "@landlord_user",
        }
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"✓ Created User: id={db_user.id}, email='{db_user.email}'")

        # Step 2: Create Landlord linked to User (One-to-One)
        print("\nStep 2: Creating Landlord linked to User...")
        landlord_data = {
            "user_id": db_user.id,
            "first_name": "John",
            "last_name": "Doe",
        }
        db_landlord = Landlord(**landlord_data)
        db.add(db_landlord)
        db.commit()
        db.refresh(db_landlord)
        print(
            f"✓ Created Landlord: id={db_landlord.id}, name='{db_landlord.first_name} {db_landlord.last_name}'"
        )
        print(f"  Linked to User id={db_landlord.user_id}")

        # Step 3: Create First Apartment linked to Landlord (One-to-Many)
        print("\nStep 3: Creating First Apartment...")
        apartment1_data = {
            "name": "Luxury Penthouse",
            "description": "Spacious penthouse with panoramic city views and modern amenities",
            "price_per_night": 200.0,
            "address": "456 Sky Tower, Saint Petersburg",
            "location": "POINT(30.3351 59.9343)",  # Saint Petersburg coordinates (lon, lat)
            "landlord_id": db_landlord.id,
        }
        db_apartment1 = Apartment(**apartment1_data)
        db.add(db_apartment1)
        db.commit()
        db.refresh(db_apartment1)
        print(f"✓ Created Apartment 1: id={db_apartment1.id}, name='{db_apartment1.name}'")
        print(f"  Linked to Landlord id={db_apartment1.landlord_id}")

        # Step 4: Create Photos for First Apartment (One-to-Many)
        print("\nStep 4: Creating Photos for First Apartment...")
        photo1_data = {
            "apartment_id": db_apartment1.id,
            "url": "https://example.com/apartments/penthouse/living-room.jpg",
        }
        db_photo1 = Photo(**photo1_data)
        db.add(db_photo1)
        db.commit()
        print(f"✓ Created Photo 1: id={db_photo1.id}, url='{db_photo1.url}'")

        photo2_data = {
            "apartment_id": db_apartment1.id,
            "url": "https://example.com/apartments/penthouse/bedroom.jpg",
        }
        db_photo2 = Photo(**photo2_data)
        db.add(db_photo2)
        db.commit()
        print(f"✓ Created Photo 2: id={db_photo2.id}, url='{db_photo2.url}'")

        photo3_data = {
            "apartment_id": db_apartment1.id,
            "url": "https://example.com/apartments/penthouse/panoramic-view.jpg",
        }
        db_photo3 = Photo(**photo3_data)
        db.add(db_photo3)
        db.commit()
        print(f"✓ Created Photo 3: id={db_photo3.id}, url='{db_photo3.url}'")

        # Step 5: Create Second Apartment for same Landlord
        print("\nStep 5: Creating Second Apartment for same Landlord...")
        apartment2_data = {
            "name": "Cozy Studio",
            "description": "A beautiful studio apartment in the city center",
            "price_per_night": 75.0,
            "address": "123 Main Street, Moscow",
            "location": "POINT(37.6173 55.7558)",  # Moscow coordinates (lon, lat)
            "landlord_id": db_landlord.id,
        }
        db_apartment2 = Apartment(**apartment2_data)
        db.add(db_apartment2)
        db.commit()
        db.refresh(db_apartment2)
        print(f"✓ Created Apartment 2: id={db_apartment2.id}, name='{db_apartment2.name}'")
        print(f"  Linked to Landlord id={db_apartment2.landlord_id}")

        # Step 6: Create Photos for Second Apartment
        print("\nStep 6: Creating Photos for Second Apartment...")
        photo4_data = {
            "apartment_id": db_apartment2.id,
            "url": "https://example.com/apartments/studio/main-room.jpg",
        }
        db_photo4 = Photo(**photo4_data)
        db.add(db_photo4)
        db.commit()
        print(f"✓ Created Photo 4: id={db_photo4.id}, url='{db_photo4.url}'")

        photo5_data = {
            "apartment_id": db_apartment2.id,
            "url": "https://example.com/apartments/studio/kitchen.jpg",
        }
        db_photo5 = Photo(**photo5_data)
        db.add(db_photo5)
        db.commit()
        print(f"✓ Created Photo 5: id={db_photo5.id}, url='{db_photo5.url}'")

        # Step 7: Verify all relationships
        print("\n" + "=" * 60)
        print("VERIFYING RELATIONSHIPS:")
        print("=" * 60)

        db.refresh(db_user)
        db.refresh(db_landlord)
        db.refresh(db_apartment1)
        db.refresh(db_apartment2)

        print(f"\n1. User '{db_user.email}' (id={db_user.id})")
        print(
            f"   └─ Has Landlord: '{db_user.landlord.first_name} {db_user.landlord.last_name}' (id={db_user.landlord.id})"
        )

        print(
            f"\n2. Landlord '{db_landlord.first_name} {db_landlord.last_name}' (id={db_landlord.id})"
        )
        print(f"   └─ Has {len(db_landlord.apartments)} apartment(s):")
        for apt in db_landlord.apartments:
            print(f"      • Apartment '{apt.name}' (id={apt.id}) with {len(apt.photos)} photo(s)")
            for photo in apt.photos:
                print(f"        - Photo {photo.id}: {photo.url}")

        print("\n" + "=" * 60)
        print("✓ Seed data created successfully!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error creating seed data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_complete_data()
