import pytest
from httpx import AsyncClient
from app.main import app
from app.services.roles import get_current_landlord
from datetime import date, timedelta

# 1. Определяем даты для поиска
check_in = date.today() + timedelta(days=1)
check_out = date.today() + timedelta(days=5)

@pytest.fixture(autouse=True)
async def setup_landlord_auth(mock_landlord_profile):
    """Автоматически авторизуем лендлорда для всех тестов поиска."""
    async def override_get_current_landlord():
        return mock_landlord_profile

    app.dependency_overrides[get_current_landlord] = override_get_current_landlord
    yield
    app.dependency_overrides.pop(get_current_landlord, None)

@pytest.mark.asyncio
async def test_search_apartments_in_radius(client: AsyncClient, sample_apartment_data):
    """Тест поиска апартаментов по координатам."""

    # 1. Создаем апартамент в конкретной точке (Москва, Красная площадь)
    # Координаты: 37.6173 (lon), 55.7558 (lat)
    sample_apartment_data["location"] = "POINT(37.6173 55.7558)"
    await client.post("/apartments/", json=sample_apartment_data)

    # 2. Ищем в радиусе 1 км, находясь в 500 метрах от точки (37.62, 55.75)
    search_params = {
        "lat": 55.75,
        "lon": 37.62,
        "radius": 1000,
        "check_in": check_in.isoformat(), 
        "check_out": check_out.isoformat()
    }

    response = await client.get("/apartments/search", params=search_params)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == sample_apartment_data["name"]

@pytest.mark.asyncio
async def test_search_apartments_out_of_radius(client: AsyncClient, sample_apartment_data):
    """Тест, что апартаменты вне радиуса не попадают в выдачу."""

    # Апартамент в Москве
    sample_apartment_data["location"] = "POINT(37.6173 55.7558)"
    await client.post("/apartments/", json=sample_apartment_data)

    # Ищем в радиусе 1 км, находясь в Санкт-Петербурге
    search_params = {
        "lat": 59.9343,
        "lon": 30.3351,
        "radius": 1000,
        "check_in": check_in.isoformat(), 
        "check_out": check_out.isoformat()
    }

    response = await client.get("/apartments/search", params=search_params)
    if response.status_code != 200:
        print(f"\nДетали ошибки 422: {response.json()}") # Это покажет, на чем именно валится Pydantic
    assert response.status_code == 200
    assert len(response.json()) == 0
