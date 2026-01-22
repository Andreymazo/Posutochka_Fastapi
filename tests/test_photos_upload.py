import pytest
from httpx import AsyncClient
from io import BytesIO

@pytest.mark.asyncio
async def test_upload_photo_full_cycle(client: AsyncClient, created_apartment):
    """
    Тест загрузки фото, использующий существующую фикстуру апартаментов.
    Это покроет основную логику в app/routers/photos.py.
    """
    # 1. Готовим файл
    file_content = b"fake-binary-image-data"
    files = {
        "file": ("apartment_photo.jpg", BytesIO(file_content), "image/jpeg")
    }
    
    # 2. Используем ID из фикстуры
    data = {
        "apartment_id": str(created_apartment.id),
        "is_main": "true"
    }

    # 3. Отправляем запрос
    response = await client.post("/photos/upload", files=files, data=data)

    # 4. Проверяем
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["apartment_id"] == created_apartment.id
    assert json_data["is_main"] is True
    assert "media/apartments/" in json_data["url"]

@pytest.mark.asyncio
async def test_upload_photo_invalid_type(client: AsyncClient):
    # Тестируем валидацию расширения (покроет ветку ошибки)
    files = {"file": ("test.txt", b"some text", "text/plain")}
    data = {"apartment_id": 1}
    
    response = await client.post("/photos/upload", files=files, data=data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Допустимы только изображения (jpg, png, webp)"

@pytest.mark.asyncio
async def test_upload_photo_not_main(client: AsyncClient, created_apartment):
    """Тест загрузки обычного (не главного) фото."""
    files = {"file": ("room.jpg", BytesIO(b"content"), "image/jpeg")}
    data = {
        "apartment_id": str(created_apartment.id),
        "is_main": "false"  # Тестируем ветку, где is_main = False
    }

    response = await client.post("/photos/upload", files=files, data=data)
    assert response.status_code == 201
    assert response.json()["is_main"] is False
