"""Test health check endpoints."""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests for health check endpoints (Async version 2026)."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient) -> None:
        """Test root endpoint returns welcome message."""
        # Добавляем await для асинхронного вызова
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to Posutochka API"}

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient) -> None:
        """Test health check endpoint returns healthy status."""
        # Добавляем await для асинхронного вызова
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"} # Убедитесь, что в коде именно 'healthy' или 'ok'
