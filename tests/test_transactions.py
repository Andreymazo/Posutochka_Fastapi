"""Tests for Transaction API endpoints."""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Booking, Transaction, User


class TestTransactionEndpoints:
    """Tests for transaction CRUD operations."""

    def test_create_transaction(
        self,
        client: TestClient,
        created_user: User,
        created_booking: Booking,
        sample_transaction_data: dict[str, Any],
    ) -> None:
        """Test creating a new transaction."""
        data = {
            **sample_transaction_data,
            "user_id": created_user.id,
            "booking_id": created_booking.id,
        }
        response = client.post("/transactions/", json=data)
        assert response.status_code == 201
        assert response.json()["amount"] == sample_transaction_data["amount"]
        assert response.json()["transaction_type"] == sample_transaction_data["transaction_type"]
        assert response.json()["user_id"] == created_user.id
        assert response.json()["booking_id"] == created_booking.id

    def test_get_transactions(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_transaction_data: dict[str, Any],
    ) -> None:
        """Test retrieving all transactions."""
        transaction = Transaction(
            amount=sample_transaction_data["amount"],
            transaction_type=sample_transaction_data["transaction_type"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(transaction)
        db_session.commit()

        response = client.get("/transactions/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_transaction_by_id(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_transaction_data: dict[str, Any],
    ) -> None:
        """Test retrieving a specific transaction by ID."""
        transaction = Transaction(
            amount=sample_transaction_data["amount"],
            transaction_type=sample_transaction_data["transaction_type"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)

        response = client.get(f"/transactions/{transaction.id}")
        assert response.status_code == 200
        assert response.json()["id"] == transaction.id
        assert response.json()["amount"] == sample_transaction_data["amount"]
        assert response.json()["transaction_type"] == sample_transaction_data["transaction_type"]

    def test_get_transaction_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent transaction."""
        response = client.get("/transactions/99999")
        assert response.status_code == 404

    def test_update_transaction(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_transaction_data: dict[str, Any],
    ) -> None:
        """Test updating a transaction."""
        transaction = Transaction(
            amount=sample_transaction_data["amount"],
            transaction_type=sample_transaction_data["transaction_type"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)

        update_data = {"amount": 300.0, "transaction_type": "refund"}
        response = client.patch(f"/transactions/{transaction.id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["amount"] == 300.0
        assert response.json()["transaction_type"] == "refund"

    def test_delete_transaction(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_transaction_data: dict[str, Any],
    ) -> None:
        """Test deleting a transaction."""
        transaction = Transaction(
            amount=sample_transaction_data["amount"],
            transaction_type=sample_transaction_data["transaction_type"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)

        response = client.delete(f"/transactions/{transaction.id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/transactions/{transaction.id}")
        assert response.status_code == 404

    def test_filter_transactions_by_user(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_transaction_data: dict[str, Any],
    ) -> None:
        """Test filtering transactions by user_id."""
        transaction = Transaction(
            amount=sample_transaction_data["amount"],
            transaction_type=sample_transaction_data["transaction_type"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(transaction)
        db_session.commit()

        response = client.get(f"/transactions/?user_id={created_user.id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert all(t["user_id"] == created_user.id for t in response.json())

    def test_filter_transactions_by_booking(
        self,
        client: TestClient,
        db_session: Session,
        created_user: User,
        created_booking: Booking,
        sample_transaction_data: dict[str, Any],
    ) -> None:
        """Test filtering transactions by booking_id."""
        transaction = Transaction(
            amount=sample_transaction_data["amount"],
            transaction_type=sample_transaction_data["transaction_type"],
            user_id=created_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(transaction)
        db_session.commit()

        response = client.get(f"/transactions/?booking_id={created_booking.id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert all(t["booking_id"] == created_booking.id for t in response.json())

    def test_transaction_types(
        self,
        client: TestClient,
        created_user: User,
        created_booking: Booking,
    ) -> None:
        """Test creating transactions with different types."""
        transaction_types = [
            "booking_payment",
            "booking_income",
            "platform_commission",
            "refund",
            "withdrawal",
        ]

        for trans_type in transaction_types:
            data = {
                "amount": 100.0,
                "transaction_type": trans_type,
                "user_id": created_user.id,
                "booking_id": created_booking.id,
            }
            response = client.post("/transactions/", json=data)
            assert response.status_code == 201
            assert response.json()["transaction_type"] == trans_type
