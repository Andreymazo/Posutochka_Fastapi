"""Tests for Balance API endpoints."""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Balance, Booking


class TestBalanceEndpoints:
    """Tests for balance CRUD operations."""

    def test_create_balance(
        self,
        client: TestClient,
        created_booking: Booking,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test creating a new balance."""
        data = {
            **sample_balance_data,
            "booking_id": created_booking.id,
        }
        response = client.post("/balances/", json=data)
        assert response.status_code == 201
        assert response.json()["amount"] == sample_balance_data["amount"]
        assert response.json()["booking_id"] == created_booking.id

    def test_get_balances(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test retrieving all balances."""
        balance = Balance(
            amount=sample_balance_data["amount"],
            booking_id=created_booking.id,
        )
        db_session.add(balance)
        db_session.commit()

        response = client.get("/balances/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_balance_by_id(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test retrieving a specific balance by ID."""
        balance = Balance(
            amount=sample_balance_data["amount"],
            booking_id=created_booking.id,
        )
        db_session.add(balance)
        db_session.commit()
        db_session.refresh(balance)

        response = client.get(f"/balances/{balance.id}")
        assert response.status_code == 200
        assert response.json()["id"] == balance.id
        assert response.json()["amount"] == sample_balance_data["amount"]

    def test_get_balance_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent balance."""
        response = client.get("/balances/99999")
        assert response.status_code == 404

    def test_update_balance(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test updating a balance."""
        balance = Balance(
            amount=sample_balance_data["amount"],
            booking_id=created_booking.id,
        )
        db_session.add(balance)
        db_session.commit()
        db_session.refresh(balance)

        update_data = {"amount": 500.0}
        response = client.patch(f"/balances/{balance.id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["amount"] == 500.0

    def test_delete_balance(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test deleting a balance."""
        balance = Balance(
            amount=sample_balance_data["amount"],
            booking_id=created_booking.id,
        )
        db_session.add(balance)
        db_session.commit()
        db_session.refresh(balance)

        response = client.delete(f"/balances/{balance.id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/balances/{balance.id}")
        assert response.status_code == 404

    def test_filter_balances_by_booking(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test filtering balances by booking_id."""
        balance = Balance(
            amount=sample_balance_data["amount"],
            booking_id=created_booking.id,
        )
        db_session.add(balance)
        db_session.commit()

        response = client.get(f"/balances/?booking_id={created_booking.id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert all(b["booking_id"] == created_booking.id for b in response.json())
