"""Tests for Owner API endpoints."""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Booking, Owner, User


class TestOwnerEndpoints:
    """Tests for owner CRUD operations."""

    def test_create_owner(
        self,
        client: TestClient,
        created_user: User,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test creating a new owner."""
        data = {
            **sample_owner_data,
            "user_id": created_user.id,
            "booking_id": created_booking.id,
        }
        response = client.post("/owners/", json=data)
        assert response.status_code == 201
        assert response.json()["amount"] == sample_owner_data["amount"]
        assert response.json()["user_id"] == created_user.id
        assert response.json()["booking_id"] == created_booking.id

    def test_get_owners(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test retrieving all owners."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        db_session.commit()

        response = client.get("/owners/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_owner_by_id(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test retrieving a specific owner by ID."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        db_session.commit()
        db_session.refresh(owner)

        response = client.get(f"/owners/{owner.id}")
        assert response.status_code == 200
        assert response.json()["id"] == owner.id
        assert response.json()["amount"] == sample_owner_data["amount"]

    def test_get_owner_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent owner."""
        response = client.get("/owners/99999")
        assert response.status_code == 404

    def test_update_owner(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test updating an owner."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        db_session.commit()
        db_session.refresh(owner)

        update_data = {"amount": 150.0}
        response = client.patch(f"/owners/{owner.id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["amount"] == 150.0

    def test_delete_owner(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test deleting an owner."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        db_session.commit()
        db_session.refresh(owner)

        response = client.delete(f"/owners/{owner.id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/owners/{owner.id}")
        assert response.status_code == 404

    def test_filter_owners_by_user(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test filtering owners by user_id."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        db_session.commit()

        response = client.get(f"/owners/?user_id={created_user.id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert all(o["user_id"] == created_user.id for o in response.json())

    def test_filter_owners_by_booking(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test filtering owners by booking_id."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        db_session.commit()

        response = client.get(f"/owners/?booking_id={created_booking.id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert all(o["booking_id"] == created_booking.id for o in response.json())
