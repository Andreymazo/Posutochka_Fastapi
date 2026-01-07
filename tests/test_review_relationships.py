"""Tests for Review relationships with Client and Landlord models."""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Booking, Client, Landlord, Review
from app.models.review import UserRole


class TestClientReviewRelationships:
    """Tests for Client review relationship fields."""

    def test_client_reviews_about_me(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test that reviews_about_me contains only reviews written by landlords about the client."""
        # Create a review by landlord about client
        landlord_review = Review(
            rating=5,
            review="Great guest!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        db_session.add(landlord_review)
        db_session.commit()
        db_session.refresh(created_client)

        # Verify reviews_about_me contains the landlord's review
        assert len(created_client.reviews_about_me) == 1
        assert created_client.reviews_about_me[0].id == landlord_review.id
        assert created_client.reviews_about_me[0].author_role.value == "landlord"

    def test_client_reviews_i_wrote(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test that reviews_i_wrote contains only reviews written by the client."""
        # Create a review by client about landlord/apartment
        client_review = Review(
            rating=4,
            review="Nice apartment!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(client_review)
        db_session.commit()
        db_session.refresh(created_client)

        # Verify reviews_i_wrote contains the client's review
        assert len(created_client.reviews_i_wrote) == 1
        assert created_client.reviews_i_wrote[0].id == client_review.id
        assert created_client.reviews_i_wrote[0].author_role.value == "client"

    def test_client_both_review_types(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test that client can have both types of reviews simultaneously."""
        # Create a review by landlord about client
        landlord_review = Review(
            rating=5,
            review="Great guest!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        # Create a review by client
        client_review = Review(
            rating=4,
            review="Nice apartment!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(landlord_review)
        db_session.add(client_review)
        db_session.commit()
        db_session.refresh(created_client)

        # Verify both types of reviews are correctly separated
        assert len(created_client.reviews_about_me) == 1
        assert len(created_client.reviews_i_wrote) == 1
        assert created_client.reviews_about_me[0].author_role.value == "landlord"
        assert created_client.reviews_i_wrote[0].author_role.value == "client"

    def test_client_read_schema_includes_reviews(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
    ) -> None:
        """Test that ClientRead schema includes review fields in API response."""
        # Create reviews
        landlord_review = Review(
            rating=5,
            review="Excellent guest",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        client_review = Review(
            rating=4,
            review="Good apartment",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(landlord_review)
        db_session.add(client_review)
        db_session.commit()

        # Get client via API
        response = client.get(f"/clients/{created_client.id}")
        assert response.status_code == 200
        data = response.json()

        # Verify review fields are present in response
        assert "reviews_about_me" in data
        assert "reviews_i_wrote" in data
        assert len(data["reviews_about_me"]) == 1
        assert len(data["reviews_i_wrote"]) == 1
        assert data["reviews_about_me"][0]["author_role"] == "landlord"
        assert data["reviews_i_wrote"][0]["author_role"] == "client"


class TestLandlordReviewRelationships:
    """Tests for Landlord review relationship fields."""

    def test_landlord_reviews_about_me(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test that reviews_about_me contains only reviews written by clients about the landlord."""
        # Create a review by client about landlord
        client_review = Review(
            rating=5,
            review="Excellent host!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(client_review)
        db_session.commit()
        db_session.refresh(created_landlord)

        # Verify reviews_about_me contains the client's review
        assert len(created_landlord.reviews_about_me) == 1
        assert created_landlord.reviews_about_me[0].id == client_review.id
        assert created_landlord.reviews_about_me[0].author_role.value == "client"

    def test_landlord_reviews_i_wrote(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test that reviews_i_wrote contains only reviews written by the landlord."""
        # Create a review by landlord about client
        landlord_review = Review(
            rating=4,
            review="Nice guest!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        db_session.add(landlord_review)
        db_session.commit()
        db_session.refresh(created_landlord)

        # Verify reviews_i_wrote contains the landlord's review
        assert len(created_landlord.reviews_i_wrote) == 1
        assert created_landlord.reviews_i_wrote[0].id == landlord_review.id
        assert created_landlord.reviews_i_wrote[0].author_role.value == "landlord"

    def test_landlord_both_review_types(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
        sample_review_data: dict[str, Any],
    ) -> None:
        """Test that landlord can have both types of reviews simultaneously."""
        # Create a review by client about landlord
        client_review = Review(
            rating=5,
            review="Excellent host!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        # Create a review by landlord about client
        landlord_review = Review(
            rating=4,
            review="Good guest!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        db_session.add(client_review)
        db_session.add(landlord_review)
        db_session.commit()
        db_session.refresh(created_landlord)

        # Verify both types of reviews are correctly separated
        assert len(created_landlord.reviews_about_me) == 1
        assert len(created_landlord.reviews_i_wrote) == 1
        assert created_landlord.reviews_about_me[0].author_role.value == "client"
        assert created_landlord.reviews_i_wrote[0].author_role.value == "landlord"

    def test_landlord_read_schema_includes_reviews(
        self,
        client: TestClient,
        db_session: Session,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
    ) -> None:
        """Test that LandlordRead schema includes review fields in API response."""
        # Create reviews
        client_review = Review(
            rating=5,
            review="Excellent host",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        landlord_review = Review(
            rating=4,
            review="Good guest",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        db_session.add(client_review)
        db_session.add(landlord_review)
        db_session.commit()

        # Get landlord via API
        response = client.get(f"/landlords/{created_landlord.id}")
        assert response.status_code == 200
        data = response.json()

        # Verify review fields are present in response
        assert "reviews_about_me" in data
        assert "reviews_i_wrote" in data
        assert len(data["reviews_about_me"]) == 1
        assert len(data["reviews_i_wrote"]) == 1
        assert data["reviews_about_me"][0]["author_role"] == "client"
        assert data["reviews_i_wrote"][0]["author_role"] == "landlord"
