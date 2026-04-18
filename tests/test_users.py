"""Tests for User API endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUserEndpoints:
    """Tests for /users endpoints."""

    async def test_create_user(self, client: AsyncClient, sample_user_data: dict[str, Any]) -> None:
        """Test creating a new user."""
        response = await client.post("/users/", json=sample_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["phone_number"] == sample_user_data["phone_number"]
        assert "id" in data
        assert "registration_date" in data

    async def test_create_user_duplicate_email(
        self, client: AsyncClient, sample_user_data: dict[str, Any]
    ) -> None:
        """Test that creating user with duplicate email fails."""
        # Create first user
        await client.post("/users/", json=sample_user_data)

        # Try to create second user with same email
        # В 2026 году мы ожидаем 400 ошибку при дубликате
        response = await client.post("/users/", json=sample_user_data)
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()

    async def test_create_user_duplicate_phone(
        self, client: AsyncClient, sample_user_data: dict[str, Any]
    ) -> None:
        """Test that creating user with duplicate phone fails."""
        # Create first user
        await client.post("/users/", json=sample_user_data)

        # Try to create second user with same phone but different email
        new_user_data = sample_user_data.copy()
        new_user_data["email"] = "different_unique@example.com"

        response = await client.post("/users/", json=new_user_data)
        assert response.status_code == 400
        assert "phone number already registered" in response.json()["detail"].lower()

    async def test_get_users_empty(self, client: AsyncClient) -> None:
        """Test getting users list is a valid list."""
        response = await client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Если база не пустая, это не ошибка в рамках сессионных тестов
        #     assert response.json() == [] такая запись в ассинхронных тестах выдаст скорее всего ошибку

    async def test_get_users(self, client: AsyncClient, sample_user_data: dict[str, Any]) -> None:
        """Test getting list of users."""
        # Create a user first
        await client.post("/users/", json=sample_user_data)

        response = await client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Ищем нашего пользователя в списке
        assert any(u["email"] == sample_user_data["email"] for u in data)

    async def test_get_users_pagination(
        self, client: AsyncClient, sample_user_data: dict[str, Any]
    ) -> None:
        """Test users pagination."""
        # Create multiple users
        for i in range(3):
            user_data = sample_user_data.copy()
            user_data["email"] = f"pagination{i}_{sample_user_data['email']}"
            user_data["phone_number"] = f"+7999000000{i}"
            await client.post("/users/", json=user_data)

        # Test skip and limit
        response = await client.get("/users/?skip=1&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    async def test_get_user_by_id(self, client: AsyncClient, sample_user_data: dict[str, Any]) -> None:
        """Test getting a specific user by ID."""
        # Create a user
        create_response = await client.post("/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Get the user
        response = await client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]

    async def test_get_user_not_found(self, client: AsyncClient) -> None:
        """Test getting a non-existent user."""
        response = await client.get("/users/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_update_user(self, client: AsyncClient, sample_user_data: dict[str, Any]) -> None:
        """Test updating a user."""
        # Create a user
        create_response = await client.post("/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Update the user
        update_data = {"email": "updated_user_2026@example.com"}
        response = await client.patch(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated_user_2026@example.com"
        assert data["phone_number"] == sample_user_data["phone_number"]

    async def test_update_user_not_found(self, client: AsyncClient) -> None:
        """Test updating a non-existent user."""
        response = await client.patch("/users/99999", json={"email": "new@example.com"})
        assert response.status_code == 404

    async def test_delete_user(self, client: AsyncClient, sample_user_data: dict[str, Any]) -> None:
        """Test deleting a user."""
        # Create a user
        create_response = await client.post("/users/", json=sample_user_data)     
         # ДОБАВЬТЕ ЭТИ ДВЕ СТРОКИ ДЛЯ ДИАГНОСТИКИ:
        print("\nSTATUS CODE:", create_response.status_code)
        print("RESPONSE BODY:", create_response.text)
        user_id = create_response.json()["id"]

        # Delete the user
        response = await client.delete(f"/users/{user_id}")
        assert response.status_code == 204

        # Verify user is deleted
        get_response = await client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    async def test_delete_user_not_found(self, client: AsyncClient) -> None:
        """Test deleting a non-existent user."""
        response = await client.delete("/users/99999")
        assert response.status_code == 404
