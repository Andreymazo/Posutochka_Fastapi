"""Tests for Review API endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, Client, Landlord, Review
from app.models.review import UserRole


@pytest.mark.asyncio
class TestReviewEndpoints:
    """Tests for review CRUD operations (Async version 2026)."""

    async def test_create_review(
        self,
        client: AsyncClient,
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
        response = await client.post("/reviews/", json=data)
        assert response.status_code == 201
        res_data = response.json()
        assert res_data["rating"] == sample_review_data["rating"]
        assert res_data["review"] == sample_review_data["review"]
        assert res_data["author_role"] == "CLIENT"

    async def test_get_reviews(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
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
        await db_session.commit()

        response = await client.get("/reviews/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    async def test_get_review_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
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
        await db_session.commit()
        await db_session.refresh(review)

        response = await client.get(f"/reviews/{review.id}")
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["id"] == review.id
        assert res_data["rating"] == sample_review_data["rating"]

    async def test_get_review_not_found(self, client: AsyncClient) -> None:
        """Test retrieving a non-existent review."""
        response = await client.get("/reviews/99999")
        assert response.status_code == 404

    async def test_update_review(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
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
        await db_session.commit()
        await db_session.refresh(review)

        update_data = {"rating": 4, "review": "Updated review text"}
        response = await client.patch(f"/reviews/{review.id}", json=update_data)
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["rating"] == 4
        assert res_data["review"] == "Updated review text"

    async def test_delete_review(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
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
        await db_session.commit()
        await db_session.refresh(review)

        response = await client.delete(f"/reviews/{review.id}")
        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f"/reviews/{review.id}")
        assert response.status_code == 404

    async def test_filter_reviews_by_booking(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
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
        await db_session.commit()

        response = await client.get(f"/reviews/?booking_id={created_booking.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(r["booking_id"] == created_booking.id for r in data)

    async def test_filter_reviews_by_landlord(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
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
        await db_session.commit()

        response = await client.get(f"/reviews/?landlord_id={created_landlord.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(r["landlord_id"] == created_landlord.id for r in data)

    async def test_filter_reviews_by_client(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
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
        await db_session.commit()

        response = await client.get(f"/reviews/?client_id={created_client.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(r["client_id"] == created_client.id for r in data)
