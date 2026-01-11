"""Seed script to create an apartment with multiple photos.

Demonstrates one-to-many relationship: one Apartment has multiple Photos.
Run with: python -m seed_create_apartment_with_photos
"""

from app.database import SessionLocal
from app.models.apartment import Apartment
from app.models.photo import Photo


def create_apartment_with_photos() -> None:
    """Create an apartment with three photos to demonstrate one-to-many relationship."""
    db = SessionLocal()

    try:
        # Create apartment
        apartment_data = {
            "name": "Luxury Penthouse",
            "description": "Spacious penthouse with panoramic city views and modern amenities",
            "price_per_night": 200.0,
            "address": "456 Sky Tower, Saint Petersburg",
            "location": "POINT(30.3351 59.9343)",  # Saint Petersburg coordinates (lon, lat)
        }
        db_apartment = Apartment(**apartment_data)
        db.add(db_apartment)
        db.commit()
        print(f"Created apartment: id={db_apartment.id}, name='{db_apartment.name}'")

        # Create first photo (living room)
        photo1_data = {
            "apartment_id": db_apartment.id,
            "url": "https://example.com/apartments/penthouse/living-room.jpg",
        }
        db_photo1 = Photo(**photo1_data)
        db.add(db_photo1)
        db.commit()
        print(f"Created photo 1: id={db_photo1.id}, url='{db_photo1.url}'")

        # Create second photo (bedroom)
        photo2_data = {
            "apartment_id": db_apartment.id,
            "url": "https://example.com/apartments/penthouse/bedroom.jpg",
        }
        db_photo2 = Photo(**photo2_data)
        db.add(db_photo2)
        db.commit()
        print(f"Created photo 2: id={db_photo2.id}, url='{db_photo2.url}'")

        # Create third photo (view)
        photo3_data = {
            "apartment_id": db_apartment.id,
            "url": "https://example.com/apartments/penthouse/panoramic-view.jpg",
        }
        db_photo3 = Photo(**photo3_data)
        db.add(db_photo3)
        db.commit()
        print(f"Created photo 3: id={db_photo3.id}, url='{db_photo3.url}'")

        # Verify one-to-many relationship
        db.refresh(db_apartment)
        print("\nVerifying relationship:")
        print(f"Apartment '{db_apartment.name}' has {len(db_apartment.photos)} photo(s):")
        for photo in db_apartment.photos:
            print(f"  - Photo {photo.id}: {photo.url}")

        print("\nSeed data created successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error creating seed data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_apartment_with_photos()
