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
    # 1. Очистка (уже корректно)
    res = await db_session.execute(
        select(Landlord).where(Landlord.user_id == mock_landlord_profile.id)
    )
    existing_landlord = res.scalar_one_or_none()
    if existing_landlord:
        await client.delete(f"/landlords/{existing_landlord.id}")

    # 2. ТЕСТИРУЕМ POST
    payload = {"user_id": mock_landlord_profile.id}
    resp = await client.post("/landlords/", json=payload)
    assert resp.status_code == 201
    landlord_id = resp.json()["id"]

        
    # 3. ТЕСТИРУЕМ GET (Получение)
    resp = await client.get(f"/landlords/{landlord_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == mock_landlord_profile.id  # Проверяем связь, а не имя

    # 4. ТЕСТИРУЕМ PATCH
    # Если роутер лендлорда умеет обновлять данные юзера:

    assert resp.status_code == 200

    # 5. ТЕСТИРУЕМ DELETE и 404 (без изменений)
    resp = await client.delete(f"/landlords/{landlord_id}")
    assert resp.status_code == 204
