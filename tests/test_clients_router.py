import pytest
from httpx import AsyncClient
from starlette import status
from sqlalchemy import select
from app.models import Client  # Импортируем только то, что нужно

@pytest.mark.asyncio
async def test_client_lifecycle(client: AsyncClient, db_session, mock_client_profile):
    # 1. Ищем существующего КЛИЕНТА
    res = await db_session.execute(
        select(Client).where(Client.user_id == mock_client_profile.id)
    )
    existing_client = res.scalar_one_or_none()

    if existing_client:
        await client.delete(f"/clients/{existing_client.id}")

    # 2. ТЕСТИРУЕМ POST (Создание клиента)
    # Убираем ФИО из payload, так как они уже есть в User (mock_client_profile)
    payload = {
        "user_id": mock_client_profile.id
    }
    resp = await client.post("/clients/", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    client_id = resp.json()["id"]

    # 3. ТЕСТИРУЕМ GET (Получение)
    resp = await client.get(f"/clients/{client_id}")
    assert resp.status_code == 200
    # ВАЖНО: Мы не проверяем имя здесь, так как оно в User. 
    # Если нужно проверить имя, проверяем mock_client_profile.first_name

    # 4. ТЕСТИРУЕМ PATCH (Обновление)
    # Если вы хотите обновить имя, это делается через /users/{id}
    # В /clients/ теперь обновляются только специфичные для клиента поля.
    # Если полей в ClientUpdate нет, этот шаг можно пропустить или 
    # тестировать обновление мета-данных (например, статус лояльности).
    
    # 5. ТЕСТИРУЕМ 404
    resp = await client.get("/clients/999999")
    assert resp.status_code == 404

    # 6. ТЕСТИРУЕМ DELETE
    resp = await client.delete(f"/clients/{client_id}")
    assert resp.status_code == 204
    
    # Список
    resp_list = await client.get("/clients/")
    assert resp_list.status_code == 200
