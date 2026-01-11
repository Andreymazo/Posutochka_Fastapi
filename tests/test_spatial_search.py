import pytest
from httpx import AsyncClient


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
        "radius": 1000
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
        "radius": 1000
    }

    response = await client.get("/apartments/search", params=search_params)
    if response.status_code != 200:
        print(f"\nДетали ошибки 422: {response.json()}") # Это покажет, на чем именно валится Pydantic
    assert response.status_code == 200
    assert len(response.json()) == 0
