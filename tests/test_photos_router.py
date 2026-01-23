import pytest
from httpx import AsyncClient
from starlette import status
from app.main import app
from app.services.roles import get_current_landlord

@pytest.mark.asyncio
async def test_photos_full_lifecycle(
    client: AsyncClient, 
    db_session, 
    created_apartment  # Используем существующую фикстуру апартаментов
):
    """
    Тест покрывает все ветки photos.py.
    """
    apartment_id = created_apartment.id

    # 1. POST /photos/ - Создание (строки 39-43)
    photo_payload = {
        "apartment_id": apartment_id,
        "url": "http://example.com/main.jpg",
        "is_main": True
    }
    response = await client.post("/photos/", json=photo_payload)
    assert response.status_code == status.HTTP_201_CREATED
    photo_id = response.json()["id"]

    # 2. GET /photos/ - Список с фильтром (строки 17-22)
    # Проверяем ветку 'if apartment_id'
    response = await client.get("/photos/", params={"apartment_id": apartment_id})
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["url"] == "http://example.com/main.jpg"

    # Проверяем ветку без фильтра (чтобы закрыть Branch Coverage)
    response = await client.get("/photos/")
    assert response.status_code == 200

    # 3. GET /photos/{photo_id} - Получение одного (строки 28-33)
    response = await client.get(f"/photos/{photo_id}")
    assert response.status_code == 200
    assert response.json()["id"] == photo_id

    # 3. GET /photos/{photo_id} - Получение одного (проверка, что фото есть)
    response = await client.get(f"/photos/{photo_id}")
    assert response.status_code == 200

    # 4. DELETE /photos/{photo_id} - Удаление под авторизацией
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.user import User

    # Берем владельца
    res = await db_session.execute(
        select(User)
        .options(selectinload(User.landlord))
        .where(User.id == created_apartment.landlord.user_id)
    )
    owner_user = res.scalar_one()

    app.dependency_overrides[get_current_landlord] = lambda: owner_user

    try:
        # УДАЛЯЕМ ФОТО
        response = await client.delete(f"/photos/{photo_id}")
        assert response.status_code == 204
        
        # 5. ПРОВЕРКА 404 (Удаление уже удаленного или несуществующего)
        response = await client.delete("/photos/999999")
        assert response.status_code == 404
        
        # Проверка 404 для GET
        response = await client.get(f"/photos/{photo_id}") # Это фото мы только что удалили
        assert response.status_code == 404
        
    finally:
        app.dependency_overrides.pop(get_current_landlord, None)