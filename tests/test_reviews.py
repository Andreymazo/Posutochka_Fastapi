"""Tests for Review API endpoints."""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Booking, Client, Landlord, Review
from app.models.review import UserRole


class TestReviewEndpoints:
    """Tests for review CRUD operations."""

    def test_create_review(
        self,
        client: TestClient,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test creating a new review."""
        data = {
            **sample_review_data,
            "booking_id": created_booking.id,
            "landlord_id": created_landlord.id,
            "client_id": created_client.id,
            "author_role": "CLIENT",
        }
        response = client.post("/reviews/", json=data)
        assert response.status_code == 201
        assert response.json()["rating"] == sample_review_data["rating"]
        assert response.json()["review"] == sample_review_data["review"]
        assert response.json()["author_role"] == "CLIENT"

    def test_get_reviews(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test retrieving all reviews."""
        review = Review(
            rating=sample_review_data["rating"],
            review=sample_review_data["review"],
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(review)
        db_session.commit()

        response = client.get("/reviews/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_get_review_by_id(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test retrieving a specific review by ID."""
        review = Review(
            rating=sample_review_data["rating"],
            review=sample_review_data["review"],
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        response = client.get(f"/reviews/{review.id}")
        assert response.status_code == 200
        assert response.json()["id"] == review.id
        assert response.json()["rating"] == sample_review_data["rating"]

    def test_get_review_not_found(self, client: TestClient) -> None:
        """Test retrieving a non-existent review."""
        response = client.get("/reviews/99999")
        assert response.status_code == 404

    def test_update_review(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test updating a review."""
        review = Review(
            rating=sample_review_data["rating"],
            review=sample_review_data["review"],
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        update_data = {"rating": 4, "review": "Updated review text"}
        response = client.patch(f"/reviews/{review.id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["rating"] == 4
        assert response.json()["review"] == "Updated review text"

    def test_delete_review(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test deleting a review."""
        review = Review(
            rating=sample_review_data["rating"],
            review=sample_review_data["review"],
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        response = client.delete(f"/reviews/{review.id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/reviews/{review.id}")
        assert response.status_code == 404

    def test_filter_reviews_by_booking(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test filtering reviews by booking_id."""
        review = Review(
            rating=sample_review_data["rating"],
            review=sample_review_data["review"],
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(review)
        db_session.commit()

        response = client.get(f"/reviews/?booking_id={created_booking.id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert all(r["booking_id"] == created_booking.id for r in response.json())

    def test_filter_reviews_by_landlord(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test filtering reviews by landlord_id."""
        review = Review(
            rating=sample_review_data["rating"],
            review=sample_review_data["review"],
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(review)
        db_session.commit()

        response = client.get(f"/reviews/?landlord_id={created_landlord.id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert all(r["landlord_id"] == created_landlord.id for r in response.json())

    def test_filter_reviews_by_client(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test filtering reviews by client_id."""
        review = Review(
            rating=sample_review_data["rating"],
            review=sample_review_data["review"],
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(review)
        db_session.commit()

        response = client.get(f"/reviews/?client_id={created_client.id}")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert all(r["client_id"] == created_client.id for r in response.json())
