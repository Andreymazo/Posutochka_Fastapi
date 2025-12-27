"""Tests for User API endpoints."""

from typing import Any

from fastapi.testclient import TestClient


class TestUserEndpoints:
    """Tests for /users endpoints."""

    def test_create_user(self, client: TestClient, sample_user_data: dict[str, Any]) -> None:
        """Test creating a new user."""
        response = client.post("/users/", json=sample_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["phone_number"] == sample_user_data["phone_number"]
        assert data["role"] == sample_user_data["role"]
        assert "id" in data
        assert "registration_date" in data

    def test_create_user_duplicate_email(
        self, client: TestClient, sample_user_data: dict[str, Any]
    ) -> None:
        """Test that creating user with duplicate email fails."""
        # Create first user
        client.post("/users/", json=sample_user_data)

        # Try to create second user with same email
        response = client.post("/users/", json=sample_user_data)
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()

    def test_create_user_duplicate_phone(
        self, client: TestClient, sample_user_data: dict[str, Any]
    ) -> None:
        """Test that creating user with duplicate phone fails."""
        # Create first user
        client.post("/users/", json=sample_user_data)

        # Try to create second user with same phone
        new_user_data = sample_user_data.copy()
        new_user_data["email"] = "different@example.com"
        response = client.post("/users/", json=new_user_data)
        assert response.status_code == 400
        assert "phone number already registered" in response.json()["detail"].lower()

    def test_get_users_empty(self, client: TestClient) -> None:
        """Test getting users when none exist."""
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_users(self, client: TestClient, sample_user_data: dict[str, Any]) -> None:
        """Test getting list of users."""
        # Create a user first
        client.post("/users/", json=sample_user_data)

        response = client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == sample_user_data["email"]

    def test_get_users_pagination(
        self, client: TestClient, sample_user_data: dict[str, Any]
    ) -> None:
        """Test users pagination."""
        # Create multiple users
        for i in range(3):
            user_data = sample_user_data.copy()
            user_data["email"] = f"user{i}@example.com"
            user_data["phone_number"] = f"+123456789{i}"
            client.post("/users/", json=user_data)

        # Test skip and limit
        response = client.get("/users/?skip=1&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_user_by_id(self, client: TestClient, sample_user_data: dict[str, Any]) -> None:
        """Test getting a specific user by ID."""
        # Create a user
        create_response = client.post("/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Get the user
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]

    def test_get_user_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent user."""
        response = client.get("/users/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_user(self, client: TestClient, sample_user_data: dict[str, Any]) -> None:
        """Test updating a user."""
        # Create a user
        create_response = client.post("/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Update the user
        update_data = {"email": "updated@example.com"}
        response = client.patch(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        # Other fields should remain unchanged
        assert data["phone_number"] == sample_user_data["phone_number"]

    def test_update_user_not_found(self, client: TestClient) -> None:
        """Test updating a non-existent user."""
        response = client.patch("/users/99999", json={"email": "new@example.com"})
        assert response.status_code == 404

    def test_delete_user(self, client: TestClient, sample_user_data: dict[str, Any]) -> None:
        """Test deleting a user."""
        # Create a user
        create_response = client.post("/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Delete the user
        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 204

        # Verify user is deleted
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client: TestClient) -> None:
        """Test deleting a non-existent user."""
        response = client.delete("/users/99999")
        assert response.status_code == 404
