import pytest
from httpx import AsyncClient
from starlette import status
import pytest
from httpx import AsyncClient
from starlette import status
from app.models import User, Landlord
from sqlalchemy import select
import pytest
from httpx import AsyncClient
from starlette import status

import pytest
from httpx import AsyncClient
from starlette import status
from sqlalchemy import select
from app.models import Landlord

@pytest.mark.asyncio
async def test_landlord_lifecycle(client: AsyncClient, db_session, mock_landlord_profile):
    # 1. Проверяем наличие лендлорда через явный асинхронный запрос
    # Это решает проблему MissingGreenlet
    res = await db_session.execute(
        select(Landlord).where(Landlord.user_id == mock_landlord_profile.id)
    )
    existing_landlord = res.scalar_one_or_none()

    if existing_landlord:
        # Если фикстура создала лендлорда, удаляем его через API для теста POST
        await client.delete(f"/landlords/{existing_landlord.id}")

    # 2. ТЕСТИРУЕМ POST (Создание)
    payload = {
        "user_id": mock_landlord_profile.id,
        "first_name": "Тест",
        "last_name": "Арендодателев"
    }
    resp = await client.post("/landlords/", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    landlord_id = resp.json()["id"]

    # 3. ТЕСТИРУЕМ GET (Получение)
    resp = await client.get(f"/landlords/{landlord_id}")
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Тест"

    # 4. ТЕСТИРУЕМ PATCH (Обновление)
    resp = await client.patch(f"/landlords/{landlord_id}", json={"first_name": "Петр"})
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Петр"

    # 5. ТЕСТИРУЕМ 404
    resp = await client.get("/landlords/999999")
    assert resp.status_code == 404

    # 6. ТЕСТИРУЕМ DELETE
    resp = await client.delete(f"/landlords/{landlord_id}")
    assert resp.status_code == 204

    # Добавьте вызов списка (покроет строки 28-38)
    resp_list = await client.get("/landlords/")
    assert resp_list.status_code == 200
    await client.patch("/landlords/999999", json={"first_name": "X"})
    await client.delete("/landlords/999999")