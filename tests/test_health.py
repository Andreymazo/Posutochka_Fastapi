"""Test health check endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client that doesn't require database connection."""
    from unittest.mock import patch

    # Mock the database engine creation to avoid connection errors
    with patch("app.database.create_engine"):
        from app.main import app

        yield TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Posutochka API"}


def test_health_endpoint(client):
    """Test health check endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
