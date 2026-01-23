import pytest
from httpx import AsyncClient
from io import BytesIO
from app.main import app
from app.services.roles import get_current_landlord
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User

@pytest.mark.asyncio
async def test_upload_photo_full_cycle(
    client: AsyncClient, 
    created_apartment, 
    db_session
):
    # 1. ПОДМЕНЯЕМ РОЛЬ: берем пользователя, который ВЛАДЕЕТ этим апартаментом
    # Для этого подтягиваем юзера из связи (в твоих фикстурах это созданный лендлорд)
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.user import User

    # Получаем юзера, который реально создал этот апартамент в фикстуре
    res = await db_session.execute(
        select(User)
        .options(selectinload(User.landlord))
        .where(User.id == created_apartment.landlord.user_id)
    )
    real_owner = res.scalar_one()

    async def override_auth():
        return real_owner

    app.dependency_overrides[get_current_landlord] = override_auth

    # 2. Теперь загрузка пройдет, так как IDs совпадут
    file_content = b"fake-binary-image-data"
    files = {"file": ("photo.jpg", BytesIO(file_content), "image/jpeg")}
    data = {"apartment_id": str(created_apartment.id), "is_main": "true"}

    try:
        response = await client.post("/photos/upload", files=files, data=data)
        assert response.status_code == 201
    finally:
        app.dependency_overrides.pop(get_current_landlord, None)

@pytest.mark.asyncio
async def test_upload_photo_invalid_type(
    client: AsyncClient, 
    created_apartment, 
    db_session
):
    # 1. Берем РЕАЛЬНОГО владельца апартамента
 
    res = await db_session.execute(
        select(User)
        .options(selectinload(User.landlord))
        .where(User.id == created_apartment.landlord.user_id)
    )
    owner_user = res.scalar_one()

    # 2. Подменяем роль ВЛАДЕЛЬЦЕМ
    app.dependency_overrides[get_current_landlord] = lambda: owner_user
    
    try:
        # Теперь проверка на владение пройдет (200 OK), 
        # и код пойдет дальше к проверке расширения
        files = {"file": ("test.txt", b"some text", "text/plain")}
        data = {"apartment_id": str(created_apartment.id)}
        
        response = await client.post("/photos/upload", files=files, data=data)
        
        # Вот теперь мы точно получим 400 Bad Request из-за расширения .txt
        assert response.status_code == 400
        assert response.json()["detail"] == "Допустимы только изображения (jpg, png, webp)"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_photo_not_main(
    client: AsyncClient, 
    created_apartment, 
    db_session
):
    """Тест загрузки обычного (не главного) фото."""
    
    # 1. Получаем РЕАЛЬНОГО владельца этого апартамента
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.user import User

    res = await db_session.execute(
        select(User)
        .options(selectinload(User.landlord))
        .where(User.id == created_apartment.landlord.user_id)
    )
    owner_user = res.scalar_one()

    # 2. Подменяем роль владельцем
    app.dependency_overrides[get_current_landlord] = lambda: owner_user

    try:
        files = {"file": ("room.jpg", b"content", "image/jpeg")}
        data = {
            "apartment_id": str(created_apartment.id),
            "is_main": "false" 
        }

        response = await client.post("/photos/upload", files=files, data=data)
        
        assert response.status_code == 201
        assert response.json()["is_main"] is False
    finally:
        app.dependency_overrides.clear()