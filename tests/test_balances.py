import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import Any
from app.models import Balance, User # Замените на ваши пути импорта

class TestBalanceEndpoints:
    """Tests for /balances endpoints (Async version 2026)."""

    @pytest.mark.asyncio
    async def test_create_balance(
        self,
        client: AsyncClient,
        sample_balance_data: dict[str, Any],
        created_client_user: Any,  
    ) -> None:
        """Test creating a new balance."""
        data = {**sample_balance_data, "user_id": created_client_user.id}
      
        """Test creating a new balance."""
        data = {**sample_balance_data, "user_id": created_client_user.id}

        response = await client.post("/balances/", json=data)

        assert response.status_code == 201
        res_data = response.json()
        assert Decimal(str(res_data["current_balance"])) == Decimal(str(sample_balance_data["current_balance"]))
        assert "id" in res_data

    @pytest.mark.asyncio
    async def test_get_balances(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_client_user: Any,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test retrieving all balances."""
        balance = Balance(
            current_balance=sample_balance_data["current_balance"],
            user_id=created_client_user.id,
        )
        db_session.add(balance)
        await db_session.commit()

        response = await client.get("/balances/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_balance_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_client_user: Any, 
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test retrieving a specific balance by ID."""
        balance = Balance(
            current_balance=sample_balance_data["current_balance"],
            user_id=created_client_user.id,
        )
        db_session.add(balance)
        await db_session.commit()
        await db_session.refresh(balance)

        response = await client.get(f"/balances/{balance.id}")
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["id"] == balance.id
        assert Decimal(str(res_data["current_balance"])) == Decimal(str(sample_balance_data["current_balance"]))

    @pytest.mark.asyncio
    async def test_get_balance_not_found(self, client: AsyncClient) -> None:
        """Test retrieving a non-existent balance."""
        response = await client.get("/balances/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_balance(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_client_user: Any,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test updating a balance."""
        balance = Balance(
            current_balance=sample_balance_data["current_balance"],
            user_id=created_client_user.id,
        )
        db_session.add(balance)
        await db_session.commit()
        await db_session.refresh(balance)

        update_data = {"current_balance": 500.0}
        response = await client.patch(f"/balances/{balance.id}", json=update_data)
        assert response.status_code == 200
        assert Decimal(str(response.json()["current_balance"])) == Decimal("500.0")

    @pytest.mark.asyncio
    async def test_delete_balance(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_client_user: Any,
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test deleting a balance."""
        balance = Balance(
            current_balance=sample_balance_data["current_balance"],
            user_id=created_client_user.id,
        )
        db_session.add(balance)
        await db_session.commit()
        await db_session.refresh(balance)

        response = await client.delete(f"/balances/{balance.id}")
        assert response.status_code == 204

        # Проверка удаления
        response = await client.get(f"/balances/{balance.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_filter_balances_by_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_client_user: Any,  # Заменили здесь
        sample_balance_data: dict[str, Any],
    ) -> None:
        """Test filtering balances by user_id."""
        balance = Balance(
            current_balance=sample_balance_data["current_balance"],
            user_id=created_client_user.id, # И здесь
        )
        db_session.add(balance)
        await db_session.commit()

        response = await client.get(f"/balances/?user_id={created_client_user.id}") # И здесь
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(b["user_id"] == created_client_user.id for b in data)
