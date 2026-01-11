"""Tests for Owner API endpoints."""

from typing import Any
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Booking, Owner

class TestOwnerEndpoints:
    """Tests for owner CRUD operations (Async version 2026)."""

    @pytest.mark.asyncio
    async def test_create_owner(
        self,
        client: AsyncClient,
        created_owner_user: Any,  # Это уже созданный в БД User через OTO
        created_booking: Booking,
        sample_owner_data: dict[str, Any], # Теперь pytest её найдет
    ) -> None:
        """Test creating a new owner."""
        # Формируем данные для POST запроса
        data = {
            **sample_owner_data,
            "user_id": created_owner_user.id,
            "booking_id": created_booking.id,
        }
        
        response = await client.post("/owners/", json=data)
        
        assert response.status_code == 201
        res_json = response.json()
        assert res_json["amount"] == sample_owner_data["amount"]
        assert res_json["user_id"] == created_owner_user.id

    @pytest.mark.asyncio
    async def test_get_owners(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test retrieving all owners."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_owner_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        await db_session.commit()

        response = await client.get("/owners/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_owner_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test retrieving a specific owner by ID."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_owner_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        await db_session.commit()
        await db_session.refresh(owner)

        response = await client.get(f"/owners/{owner.id}")
        assert response.status_code == 200
        assert response.json()["id"] == owner.id
        assert response.json()["amount"] == sample_owner_data["amount"]

    @pytest.mark.asyncio
    async def test_get_owner_not_found(self, client: AsyncClient) -> None:
        """Test retrieving a non-existent owner."""
        response = await client.get("/owners/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_owner(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test updating an owner."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_owner_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        await db_session.commit()
        await db_session.refresh(owner)

        update_data = {"amount": 150.0}
        response = await client.patch(f"/owners/{owner.id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["amount"] == 150.0

    @pytest.mark.asyncio
    async def test_delete_owner(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test deleting an owner."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_owner_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        await db_session.commit()
        await db_session.refresh(owner)

        response = await client.delete(f"/owners/{owner.id}")
        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f"/owners/{owner.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_filter_owners_by_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test filtering owners by user_id."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_owner_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        await db_session.commit()

        response = await client.get(f"/owners/?user_id={created_owner_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(o["user_id"] == created_owner_user.id for o in data)

    @pytest.mark.asyncio
    async def test_filter_owners_by_booking(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        created_booking: Booking,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test filtering owners by booking_id."""
        owner = Owner(
            amount=sample_owner_data["amount"],
            user_id=created_owner_user.id,
            booking_id=created_booking.id,
        )
        db_session.add(owner)
        await db_session.commit()

        response = await client.get(f"/owners/?booking_id={created_booking.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(o["booking_id"] == created_booking.id for o in data)