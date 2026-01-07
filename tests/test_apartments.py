"""Tests for Apartment API endpoints."""

from typing import Any

import pytest
from fastapi.testclient import TestClient


class TestApartmentEndpoints:
    """Tests for /apartments endpoints."""

    def test_create_apartment(
        self, client: TestClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test creating a new apartment."""
        print("sample_apartment_data=============================", sample_apartment_data)
        response = client.post("/apartments/", json=sample_apartment_data)
        print("data==============================", response.__dict__)
        assert response.status_code == 201
        data = response.json()

        assert data["name"] == sample_apartment_data["name"]
        assert data["description"] == sample_apartment_data["description"]
        assert data["price_per_night"] == sample_apartment_data["price_per_night"]
        assert data["address"] == sample_apartment_data["address"]
        assert data["location"] == sample_apartment_data["location"]
        assert "id" in data

    @pytest.mark.asyncio  # ДОБАВИТЬ ЭТО
    async def test_create_apartment_without_description(  # ДОБАВИТЬ async
        self, client: TestClient, created_landlord
    ) -> None:
        """Test creating apartment without optional description."""
        apartment_data = {
            "name": "Simple Studio",
            "price_per_night": 40.0,
            "address": "456 Oak Avenue",
            "location": "POINT(30.3351 59.9343)",
            "landlord_id": created_landlord.id,
        }
        response = client.post("/apartments/", json=apartment_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Studio"
        assert data["description"] is None

    def test_create_apartment_invalid_price(self, client: TestClient, created_landlord) -> None:
        """Test that creating apartment with invalid price fails."""
        apartment_data = {
            "name": "Test Apartment",
            "price_per_night": -50.0,
            "address": "123 Main Street",
            "location": "POINT(30.3351 59.9343)",
            "landlord_id": created_landlord.id,
        }
        response = client.post("/apartments/", json=apartment_data)
        assert response.status_code == 422  # Validation error

    def test_get_apartments_empty(self, client: TestClient) -> None:
        """Test getting apartments when none exist."""
        response = client.get("/apartments/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_apartments(
        self, client: TestClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test getting list of apartments."""
        # Create an apartment first
        client.post("/apartments/", json=sample_apartment_data)

        response = client.get("/apartments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == sample_apartment_data["name"]

    def test_get_apartments_pagination(
        self, client: TestClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test apartments pagination."""
        # Create multiple apartments
        for i in range(5):
            apt_data = sample_apartment_data.copy()
            apt_data["name"] = f"Apartment {i}"
            apt_data["address"] = f"Address {i}"
            client.post("/apartments/", json=apt_data)

        # Test skip and limit
        response = client.get("/apartments/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_apartment_by_id(
        self, client: TestClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test getting a specific apartment by ID."""
        # Create an apartment
        create_response = client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Get the apartment
        response = client.get(f"/apartments/{apartment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == apartment_id
        assert data["name"] == sample_apartment_data["name"]

    def test_get_apartment_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent apartment."""
        response = client.get("/apartments/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_apartment(
        self, client: TestClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test updating an apartment."""
        # Create an apartment
        create_response = client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Update the apartment
        update_data = {"name": "Updated Apartment", "price_per_night": 75.0}
        response = client.patch(f"/apartments/{apartment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Apartment"
        assert data["price_per_night"] == 75.0
        # Other fields should remain unchanged
        assert data["address"] == sample_apartment_data["address"]

    def test_update_apartment_partial(
        self, client: TestClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test partial update of an apartment."""
        # Create an apartment
        create_response = client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Update only one field
        update_data = {"description": "New description"}
        response = client.patch(f"/apartments/{apartment_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"
        assert data["name"] == sample_apartment_data["name"]  # Unchanged

    def test_update_apartment_not_found(self, client: TestClient) -> None:
        """Test updating a non-existent apartment."""
        response = client.patch("/apartments/99999", json={"name": "New Name"})
        assert response.status_code == 404

    def test_delete_apartment(
        self, client: TestClient, sample_apartment_data: dict[str, Any]
    ) -> None:
        """Test deleting an apartment."""
        # Create an apartment
        create_response = client.post("/apartments/", json=sample_apartment_data)
        apartment_id = create_response.json()["id"]

        # Delete the apartment
        response = client.delete(f"/apartments/{apartment_id}")
        assert response.status_code == 204

        # Verify apartment is deleted
        get_response = client.get(f"/apartments/{apartment_id}")
        assert get_response.status_code == 404

    def test_delete_apartment_not_found(self, client: TestClient) -> None:
        """Test deleting a non-existent apartment."""
        response = client.delete("/apartments/99999")
        assert response.status_code == 404
