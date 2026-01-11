"""Tests for Review relationships with Client and Landlord models."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, Client, Landlord, Review
from app.models.review import UserRole


@pytest.mark.asyncio
class TestClientReviewRelationships:
    """Tests for Client review relationship fields."""

    async def test_client_reviews_about_me(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
    ) -> None:
        """Test that reviews_about_me contains only reviews written by landlords about the client."""
        landlord_review = Review(
            rating=5,
            review="Great guest!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        db_session.add(landlord_review)
        await db_session.commit()

        # В асинхронном режиме нужно явно обновить объект и подгрузить коллекции
        await db_session.refresh(created_client, ["reviews_about_me"])

        assert len(created_client.reviews_about_me) == 1
        assert created_client.reviews_about_me[0].id == landlord_review.id
        assert created_client.reviews_about_me[0].author_role == UserRole.LANDLORD


    async def test_client_reviews_i_wrote(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
    ) -> None:
        """Test that reviews_i_wrote contains only reviews written by the client."""
        client_review = Review(
            rating=4,
            review="Nice apartment!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(client_review)
        await db_session.commit()
        await db_session.refresh(created_client, ["reviews_i_wrote"])

        assert len(created_client.reviews_i_wrote) == 1
        assert created_client.reviews_i_wrote[0].id == client_review.id
        assert created_client.reviews_i_wrote[0].author_role == UserRole.CLIENT

    async def test_client_both_review_types(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
    ) -> None:
        """Test that client can have both types of reviews simultaneously."""
        landlord_review = Review(
            rating=5,
            review="Great guest!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        client_review = Review(
            rating=4,
            review="Nice apartment!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add_all([landlord_review, client_review])
        await db_session.commit()
        await db_session.refresh(created_client, ["reviews_about_me", "reviews_i_wrote"])

        assert len(created_client.reviews_about_me) == 1
        assert len(created_client.reviews_i_wrote) == 1
        assert created_client.reviews_about_me[0].author_role == UserRole.LANDLORD
        assert created_client.reviews_i_wrote[0].author_role == UserRole.CLIENT

    async def test_client_read_schema_includes_reviews(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
    ) -> None:
        """Test that ClientRead schema includes review fields in API response."""
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
        db_session.add_all([landlord_review, client_review])
        await db_session.commit()

        response = await client.get(f"/clients/{created_client.id}")
        assert response.status_code == 200
        data = response.json()

        assert "reviews_about_me" in data
        assert "reviews_i_wrote" in data
        assert len(data["reviews_about_me"]) == 1
        assert len(data["reviews_i_wrote"]) == 1


@pytest.mark.asyncio
class TestLandlordReviewRelationships:
    """Tests for Landlord review relationship fields."""

    async def test_landlord_reviews_about_me(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
    ) -> None:
        """Test that reviews_about_me contains reviews written by clients."""
        client_review = Review(
            rating=5,
            review="Excellent host!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.CLIENT,
        )
        db_session.add(client_review)
        await db_session.commit()
        await db_session.refresh(created_landlord, ["reviews_about_me"])

        assert len(created_landlord.reviews_about_me) == 1
        assert created_landlord.reviews_about_me[0].author_role == UserRole.CLIENT

    async def test_landlord_reviews_i_wrote(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_booking: Booking,
        created_landlord: Landlord,
        created_client: Client,
    ) -> None:
        """Test that reviews_i_wrote contains reviews written by the landlord."""
        landlord_review = Review(
            rating=4,
            review="Nice guest!",
            booking_id=created_booking.id,
            landlord_id=created_landlord.id,
            client_id=created_client.id,
            author_role=UserRole.LANDLORD,
        )
        db_session.add(landlord_review)
        await db_session.commit()
        await db_session.refresh(created_landlord, ["reviews_i_wrote"])

        assert len(created_landlord.reviews_i_wrote) == 1
        assert created_landlord.reviews_i_wrote[0].author_role == UserRole.LANDLORD
