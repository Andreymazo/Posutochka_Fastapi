"""Tests for Owner API endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, Owner


"""Tests for Owner API endpoints (Updated for 2026 Models)."""

from typing import Any
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Owner


class TestOwnerEndpoints:
    """Tests for owner CRUD operations (Async version 2026)."""

    @pytest.mark.asyncio
    async def test_create_owner(
        self,
        client: AsyncClient,
        created_owner_user: Any,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test creating a new owner role."""
        data = {
            **sample_owner_data,
            "user_id": created_owner_user.id,
        }

        response = await client.post("/owners/", json=data)

        assert response.status_code == 201
        res_json = response.json()
        # Сравниваем float, так как из JSON придет число или строка
        assert float(res_json["current_share"]) == float(sample_owner_data["current_share"])
        assert res_json["user_id"] == created_owner_user.id

    @pytest.mark.asyncio
    async def test_get_owners(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test retrieving all owners."""
        owner = Owner(
            current_share=sample_owner_data["current_share"],
            is_active=sample_owner_data["is_active"],
            user_id=created_owner_user.id,
        )
        db_session.add(owner)
        await db_session.commit()

        response = await client.get("/owners/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Ищем именно нашего созданного владельца в списке
        current_owner = next(o for o in data if o["user_id"] == created_owner_user.id)
        assert float(current_owner["current_share"]) == float(sample_owner_data["current_share"])

    @pytest.mark.asyncio
    async def test_get_owner_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test retrieving a specific owner by ID."""
        owner = Owner(
            current_share=sample_owner_data["current_share"],
            is_active=sample_owner_data["is_active"],
            user_id=created_owner_user.id,
        )
        db_session.add(owner)
        await db_session.commit()
        await db_session.refresh(owner)

        response = await client.get(f"/owners/{owner.id}")
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["id"] == owner.id
        assert float(res_json["current_share"]) == float(sample_owner_data["current_share"])

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
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test updating an owner's share."""
        owner = Owner(
            current_share=sample_owner_data["current_share"],
            is_active=sample_owner_data["is_active"],
            user_id=created_owner_user.id,
        )
        db_session.add(owner)
        await db_session.commit()
        await db_session.refresh(owner)

        new_share = 0.2500
        update_data = {"current_share": new_share}
        response = await client.patch(f"/owners/{owner.id}", json=update_data)
        
        assert response.status_code == 200
        assert float(response.json()["current_share"]) == new_share

    @pytest.mark.asyncio
    async def test_delete_owner(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test deleting an owner role."""
        owner = Owner(
            current_share=sample_owner_data["current_share"],
            is_active=sample_owner_data["is_active"],
            user_id=created_owner_user.id,
        )
        db_session.add(owner)
        await db_session.commit()

        response = await client.delete(f"/owners/{owner.id}")
        assert response.status_code == 204

        # Проверка удаления
        response = await client.get(f"/owners/{owner.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_filter_owners_by_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_owner_user: Any,
        sample_owner_data: dict[str, Any],
    ) -> None:
        """Test filtering owners by user_id."""
        owner = Owner(
            current_share=sample_owner_data["current_share"],
            is_active=sample_owner_data["is_active"],
            user_id=created_owner_user.id,
        )
        db_session.add(owner)
        await db_session.commit()

        response = await client.get(f"/owners/?user_id={created_owner_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(o["user_id"] == created_owner_user.id for o in data)

    # Тест фильтрации по booking_id УДАЛЕН, так как связь перенесена в OwnerEarning
