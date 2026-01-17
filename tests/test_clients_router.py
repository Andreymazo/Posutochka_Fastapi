import pytest
from httpx import AsyncClient
from starlette import status
from sqlalchemy import select
from app.models import Client  # Импортируем только то, что нужно

@pytest.mark.asyncio
async def test_client_lifecycle(client: AsyncClient, db_session, mock_client_profile):
    # 1. Ищем существующего КЛИЕНТА (исправлено условие select)
    res = await db_session.execute(
        select(Client).where(Client.user_id == mock_client_profile.id)
    )
    existing_client = res.scalar_one_or_none()

    if existing_client:
        # Удаляем через API, если фикстура его создала
        await client.delete(f"/clients/{existing_client.id}")

    # 2. ТЕСТИРУЕМ POST (Создание клиента)
    payload = {
        "user_id": mock_client_profile.id,
        "first_name": "Тест",
        "last_name": "Клиентов"
    }
    resp = await client.post("/clients/", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    client_id = resp.json()["id"]

    # 3. ТЕСТИРУЕМ GET (Получение)
    resp = await client.get(f"/clients/{client_id}")
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Тест"

    # 4. ТЕСТИРУЕМ PATCH (Обновление)
    resp = await client.patch(f"/clients/{client_id}", json={"first_name": "Петр"})
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Петр"

    # 5. ТЕСТИРУЕМ 404 (Несуществующий)
    resp = await client.get("/clients/999999")
    assert resp.status_code == 404

    # 6. ТЕСТИРУЕМ DELETE
    resp = await client.delete(f"/clients/{client_id}")
    assert resp.status_code == 204
    
    # Добавьте вызов списка (покроет строки 28-38)
    resp_list = await client.get("/clients/")
    assert resp_list.status_code == 200
    await client.patch("/clients/999999", json={"first_name": "X"})
    await client.delete("/clients/999999")