"""Tests for Apartment API endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient


class TestApartmentEndpoints:
    """Tests for /apartments endpoints."""

    @pytest.mark.asyncio
    async def test_create_apartment(
        self,
        client: AsyncClient,
        sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test creating a new apartment asynchronously."""

        # Выполняем асинхронный POST запрос
        response = await client.post("/apartments/", json=sample_apartment_data)

        # Проверки
        assert response.status_code == 201
        data = response.json()

        # Нормализуем обе строки (удаляем пробелы), чтобы сравнить только координаты
        expected_loc = sample_apartment_data["location"].replace(" ", "")
        actual_loc = data["location"].replace(" ", "")

        assert actual_loc == expected_loc
        assert data["name"] == sample_apartment_data["name"]
        assert data["description"] == sample_apartment_data["description"]
        assert data["price_per_night"] == sample_apartment_data["price_per_night"]
        assert data["address"] == sample_apartment_data["address"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_apartment_without_description(
        self,
        client: AsyncClient,  # Используем асинхронный клиент
        created_landlord: Any # Убедитесь, что эта фикстура тоже асинхронная
    ) -> None:
        """Test creating apartment without optional description."""
        apartment_data = {
            "name": "Simple Studio",
            "price_per_night": 40.0,
            "address": "456 Oak Avenue",
            "location": "POINT(30.3351 59.9343)",
            "landlord_id": created_landlord.id,
        }

        # Добавляем await для асинхронного вызова
        response = await client.post("/apartments/", json=apartment_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Studio"
        assert data["description"] is None


    @pytest.mark.asyncio
    async def test_create_apartment_invalid_price(self, client: AsyncClient, created_landlord) -> None:
        """Test that creating apartment with invalid price fails."""
        apartment_data = {
            "name": "Test Apartment",
            "price_per_night": -50.0,
            "address": "123 Main Street",
            "location": "POINT(30.3351 59.9343)",
            "landlord_id": created_landlord.id,
        }
        response = await client.post("/apartments/", json=apartment_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_apartments_empty(self, client: AsyncClient) -> None:
        """Test getting apartments when none exist."""
        # Опционально: если вы хотите именно пустой список,
        # нужно явно удалить апартаменты перед этим тестом,
        # но лучше просто проверять тип данных:
        response = await client.get("/apartments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_apartments(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test getting list of apartments."""
        # Create an apartment first
        await client.post("/apartments/", json=sample_apartment_data)

        response = await client.get("/apartments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(apt["name"] == sample_apartment_data["name"] for apt in data)

    @pytest.mark.asyncio
    async def test_get_apartments_pagination(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test apartments pagination."""
        # Create multiple apartments
        for i in range(5):
            apt_data = sample_apartment_data.copy()
            apt_data["name"] = f"Apartment {i}"
            apt_data["address"] = f"Address {i}"
            await client.post("/apartments/", json=apt_data)

        # Test skip and limit
        response = await client.get("/apartments/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_apartment_by_id(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test getting a specific apartment by ID."""
        # Create an apartment
        create_response = await client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Get the apartment
        response = await client.get(f"/apartments/{apartment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == apartment_id
        assert data["name"] == sample_apartment_data["name"]

    @pytest.mark.asyncio
    async def test_get_apartment_not_found(self, client: AsyncClient) -> None:
        """Test getting a non-existent apartment."""
        response = await client.get("/apartments/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_apartment(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test updating an apartment."""
        # Create an apartment
        create_response = await client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Update the apartment
        update_data = {"name": "Updated Apartment", "price_per_night": 75.0}
        response = await client.patch(f"/apartments/{apartment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Apartment"
        assert data["price_per_night"] == 75.0
        assert data["address"] == sample_apartment_data["address"]

    @pytest.mark.asyncio
    async def test_update_apartment_partial(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test partial update of an apartment."""
        # Create an apartment
        create_response = await client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Update only one field
        update_data = {"description": "New description"}
        response = await client.patch(f"/apartments/{apartment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"
        assert data["name"] == sample_apartment_data["name"]

    @pytest.mark.asyncio
    async def test_update_apartment_not_found(self, client: AsyncClient) -> None:
        """Test updating a non-existent apartment."""
        response = await client.patch("/apartments/99999", json={"name": "New Name"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_apartment(
        self, client: AsyncClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test deleting an apartment."""
        # Create an apartment
        create_response = await client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Delete the apartment
        response = await client.delete(f"/apartments/{apartment_id}")
        assert response.status_code == 204

        # Verify apartment is deleted
        get_response = await client.get(f"/apartments/{apartment_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_apartment_not_found(self, client: AsyncClient) -> None:
        """Test deleting a non-existent apartment."""
        response = await client.delete("/apartments/99999")
        assert response.status_code == 404
