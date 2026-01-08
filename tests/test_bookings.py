"""Tests for booking functionality with DATERANGE support."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.models.apartment import Apartment
from app.models.booking import Booking
from app.models.client import Client
from app.models.landlord import Landlord


class TestBookingDateRange:
    """Tests for DATERANGE functionality in Booking model."""

    def test_create_booking_with_daterange(
        self,
        client: TestClient,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test creating a booking with start_date and end_date (converted to DATERANGE)."""
        booking_data = {
            "start_date": "2024-03-15",
            "end_date": "2024-03-20",
            "cost": 250.0,
            "booking_status": "pending",
            "landlord_id": created_landlord.id,
            "client_id": created_client.id,
            "apartment_id": created_apartment.id,
        }

        response = client.post("/bookings/", json=booking_data)

        assert response.status_code == 201
        data = response.json()
        assert data["start_date"] == "2024-03-15"
        assert data["end_date"] == "2024-03-20"
        assert data["cost"] == 250.0
        assert data["booking_status"] == "pending"

    def test_get_booking_returns_dates_from_range(
        self,
        client: TestClient,
        db_session: Session,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test that getting a booking returns start_date and end_date from booking_period."""
        # Create booking directly in database with Range
        booking_period = Range(date(2024, 4, 1), date(2024, 4, 5), bounds="[)")
        booking = Booking(
            booking_period=booking_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )
        db_session.add(booking)
        db_session.commit()
        db_session.refresh(booking)

        response = client.get(f"/bookings/{booking.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == "2024-04-01"
        assert data["end_date"] == "2024-04-05"

    def test_update_booking_dates(
        self,
        client: TestClient,
        db_session: Session,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test updating booking dates (updates the DATERANGE)."""
        # Create initial booking
        booking_period = Range(date(2024, 5, 1), date(2024, 5, 5), bounds="[)")
        booking = Booking(
            booking_period=booking_period,
            cost=200.0,
            booking_status="pending",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )
        db_session.add(booking)
        db_session.commit()
        db_session.refresh(booking)

        # Update end_date
        update_data = {"end_date": "2024-05-10"}
        response = client.patch(f"/bookings/{booking.id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == "2024-05-01"
        assert data["end_date"] == "2024-05-10"

    def test_search_overlapping_bookings(
        self,
        db_session: Session,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test searching for apartments occupied on specific dates using DATERANGE overlap."""
        # Create several bookings for the same apartment
        booking1_period = Range(date(2024, 6, 1), date(2024, 6, 5), bounds="[)")
        booking1 = Booking(
            booking_period=booking1_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )

        booking2_period = Range(date(2024, 6, 10), date(2024, 6, 15), bounds="[)")
        booking2 = Booking(
            booking_period=booking2_period,
            cost=250.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )

        db_session.add_all([booking1, booking2])
        db_session.commit()

        # Search for bookings that overlap with June 3-7 (should find booking1)
        search_range = Range(date(2024, 6, 3), date(2024, 6, 7), bounds="[)")
        query = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range))
        occupied_apartments = db_session.execute(query).scalars().all()

        assert created_apartment.id in occupied_apartments

        # Search for bookings that overlap with June 12-20 (should find booking2)
        search_range2 = Range(date(2024, 6, 12), date(2024, 6, 20), bounds="[)")
        query2 = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range2))
        occupied_apartments2 = db_session.execute(query2).scalars().all()

        assert created_apartment.id in occupied_apartments2

        # Search for bookings that don't overlap (June 20-25)
        search_range3 = Range(date(2024, 6, 20), date(2024, 6, 25), bounds="[)")
        query3 = select(Booking.apartment_id).where(Booking.booking_period.overlaps(search_range3))
        occupied_apartments3 = db_session.execute(query3).scalars().all()

        assert created_apartment.id not in occupied_apartments3

    def test_daterange_contains_date(
        self,
        db_session: Session,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test checking if a specific date is within a booking period."""
        # Create booking for June 1-5
        booking_period = Range(date(2024, 6, 1), date(2024, 6, 5), bounds="[)")
        booking = Booking(
            booking_period=booking_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )
        db_session.add(booking)
        db_session.commit()
        db_session.refresh(booking)

        # Check if June 3 is within the booking period
        check_date = date(2024, 6, 3)
        query = select(Booking).where(Booking.booking_period.contains(check_date))
        result = db_session.execute(query).scalars().first()

        assert result is not None
        assert result.id == booking.id

        # Check if June 6 is within the booking period (should not be, end is exclusive)
        check_date2 = date(2024, 6, 6)
        query2 = select(Booking).where(Booking.booking_period.contains(check_date2))
        result2 = db_session.execute(query2).scalars().first()

        assert result2 is None

    def test_daterange_bounds_exclusive_end(
        self,
        db_session: Session,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test that DATERANGE uses [) bounds (start inclusive, end exclusive)."""
        # Create booking with [) bounds
        booking_period = Range(date(2024, 7, 1), date(2024, 7, 5), bounds="[)")
        booking = Booking(
            booking_period=booking_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )
        db_session.add(booking)
        db_session.commit()
        db_session.refresh(booking)

        # Verify the start date is included
        assert booking.booking_period.lower == date(2024, 7, 1)
        assert booking.booking_period.upper == date(2024, 7, 5)

        # Check that July 1 is included
        assert booking.booking_period.lower_inc is True
        # Check that July 5 is excluded
        assert booking.booking_period.upper_inc is False

    def test_get_all_bookings_for_apartment(
        self,
        client: TestClient,
        db_session: Session,
        created_landlord: Landlord,
        created_client: Client,
        created_apartment: Apartment,
    ) -> None:
        """Test retrieving all bookings for a specific apartment."""
        # Create multiple bookings
        booking1_period = Range(date(2024, 8, 1), date(2024, 8, 5), bounds="[)")
        booking1 = Booking(
            booking_period=booking1_period,
            cost=200.0,
            booking_status="confirmed",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )

        booking2_period = Range(date(2024, 8, 10), date(2024, 8, 15), bounds="[)")
        booking2 = Booking(
            booking_period=booking2_period,
            cost=250.0,
            booking_status="pending",
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            apartment_id=created_apartment.id,
        )

        db_session.add_all([booking1, booking2])
        db_session.commit()

        # Get all bookings for the apartment
        response = client.get(f"/bookings/?apartment_id={created_apartment.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("start_date" in booking and "end_date" in booking for booking in data)
