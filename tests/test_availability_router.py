import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_availability_rule_success(client: AsyncClient, created_apartment):
    """Тест создания правила (покрывает строки 23-33 в роутере)."""
    payload = {
        "apartment_id": created_apartment.id,
        "start_date": "2026-07-01",
        "end_date": "2026-07-10",
        "reason": "Ремонт",
        "is_blocked": True,
        "custom_price": 5500.50,
        "min_stay_days": 2
    }
    response = await client.post("/availability/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["custom_price"] == 5500.5
    assert data["start_date"] == "2026-07-01"

@pytest.mark.asyncio
async def test_get_availability_rule_not_found(client: AsyncClient):
    """Тест на ошибку 404 при получении (покрывает строки 41-44 в роутере)."""
    response = await client.get("/availability/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_update_availability_rule_not_found(client: AsyncClient):
    """Тест на ошибку 404 при обновлении (покрывает строки 61-71 в роутере)."""
    payload = {"reason": "New Reason"}
    response = await client.patch("/availability/9999", json=payload)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_availability_rule_not_found(client: AsyncClient):
    """Тест на ошибку 404 при удалении (покрывает строку 79 в роутере)."""
    response = await client.delete("/availability/9999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_apartment_availability_list(client: AsyncClient, created_apartment):
    """Тест получения списка правил для апартамента."""
    # Создаем правило через сервис или API
    await client.post("/availability/", json={
        "apartment_id": created_apartment.id,
        "start_date": "2026-08-01",
        "end_date": "2026-08-05",
        "is_blocked": True
    })
    
    response = await client.get(f"/availability/apartment/{created_apartment.id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_create_overlap_conflict_in_router(client: AsyncClient, created_apartment):
    """Тест обработки ошибки пересечения дат в роутере."""
    payload = {
        "apartment_id": created_apartment.id,
        "start_date": "2026-09-01",
        "end_date": "2026-09-10",
    }
    # Создаем первое
    await client.post("/availability/", json=payload)
    # Пытаемся создать такое же (пересечение)
    response = await client.post("/availability/", json=payload)
    
    assert response.status_code == 400
    assert "Пересекающееся правило" in response.json()["detail"]

# Тест для покрытия схемы (validator split_range)
from app.schemas.availability import AvailabilityRead
from psycopg.types.range import Range

def test_availability_read_schema_validator():
    """Покрывает строки 47-51 в app/schemas/availability.py."""
    class MockORM:
        def __init__(self):
            self.id = 1
            self.apartment_id = 1
            self.blocked_period = Range(date(2026, 12, 1), date(2026, 12, 5))
            self.reason = "Test"
            self.is_blocked = True
            self.custom_price = 100.0
            self.min_stay_days = 1

    # ВАЖНО: вызываем MockORM(), создавая экземпляр объекта
    instance = MockORM()
    
    schema_data = AvailabilityRead.model_validate(instance)
    
    assert schema_data.start_date == date(2026, 12, 1)
    assert schema_data.end_date == date(2026, 12, 5)

@pytest.mark.asyncio
async def test_get_availability_rule_success(client: AsyncClient, created_apartment):
    """Закрывает строку 53: Успешное получение правила по ID."""
    # Создаем правило
    res = await client.post("/availability/", json={
        "apartment_id": created_apartment.id,
        "start_date": "2026-10-01",
        "end_date": "2026-10-05"
    })
    rule_id = res.json()["id"]
    
    # Получаем его (вот тут сработает строка 53)
    response = await client.get(f"/availability/{rule_id}")
    assert response.status_code == 200
    assert response.json()["id"] == rule_id

@pytest.mark.asyncio
async def test_update_availability_rule_full_success(client: AsyncClient, created_apartment):
    """Закрывает строку 71: Успешное обновление правила."""
    # Создаем
    res = await client.post("/availability/", json={
        "apartment_id": created_apartment.id,
        "start_date": "2026-11-01",
        "end_date": "2026-11-05"
    })
    rule_id = res.json()["id"]
    
    # Обновляем (вот тут сработает строка 71)
    response = await client.patch(f"/availability/{rule_id}", json={"reason": "Updated Reason"})
    assert response.status_code == 200
    assert response.json()["reason"] == "Updated Reason"

def test_availability_read_without_blocked_period():
    """Закрывает переход 47->51 в схеме (случай, когда данных нет)."""
    from app.schemas.availability import AvailabilityRead
    
    # Создаем словарь без blocked_period, но с остальными полями
    raw_data = {
        "id": 1,
        "apartment_id": 1,
        "start_date": date(2026, 1, 1),
        "end_date": date(2026, 1, 2),
        "is_blocked": True,
        "min_stay_days": 1
    }
    # Валидируем просто как словарь
    data = AvailabilityRead.model_validate(raw_data)
    assert data.start_date == date(2026, 1, 1)

