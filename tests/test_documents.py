import pytest
from httpx import AsyncClient
from io import BytesIO
import os

@pytest.mark.asyncio
async def test_upload_document_success(client: AsyncClient, mock_client_profile, client_auth_headers):
    """Тест загрузки документа с использованием авторизации."""
    file_content = b"fake pdf content"
    files = {"file": ("passport.pdf", BytesIO(file_content), "application/pdf")}
    
    # Данные формы (id пользователя из фикстуры)
    data = {
        "user_id": str(mock_client_profile.id), 
        "doc_type": "passport"
    }

    # Теперь обязательно добавляем headers=client_auth_headers
    response = await client.post(
        "/documents/upload", 
        files=files, 
        data=data, 
        headers=client_auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()["status"] == "uploaded"


@pytest.mark.asyncio
async def test_get_document_success(client: AsyncClient, mock_client_profile, client_auth_headers, db_session):
    """Используем профиль клиента для скачивания документа."""
    from app.models.document import Document
    
    # 1. Создаем тестовую запись
    test_path = "media/documents/test_file.pdf"
    os.makedirs("media/documents", exist_ok=True)
    with open(test_path, "wb") as f:
        f.write(b"hello world")

    doc = Document(user_id=mock_client_profile.id, type="contract", file_path=test_path)
    db_session.add(doc)
    await db_session.commit()

    # 2. Проверяем получение
      # Делаем запрос с токеном
    response = await client.get(f"/documents/{doc.id}", headers=client_auth_headers)
    
    assert response.status_code == 200
    assert response.content == b"hello world"
    
    # Чистим диск
    if os.path.exists(test_path):
        os.remove(test_path)

@pytest.mark.asyncio
async def test_upload_document_invalid_format(client: AsyncClient, mock_client_profile, client_auth_headers):
    """Покрывает строку 25 (ошибка формата)"""
    files = {"file": ("virus.exe", BytesIO(b"content"), "application/x-msdownload")}
    data = {"user_id": str(mock_client_profile.id), "doc_type": "passport"}
    
    response = await client.post("/documents/upload", files=files, data=data, headers=client_auth_headers)
    assert response.status_code == 400
    assert "Формат файла не поддерживается" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient, client_auth_headers):
    """Покрывает строку 53 (документ не найден в БД)"""
    response = await client.get("/documents/999999", headers=client_auth_headers) # ID, которого нет
    assert response.status_code == 404
    assert "Документ не найден" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_document_file_missing_on_disk(client: AsyncClient, mock_client_profile, client_auth_headers, db_session):
    """Покрывает строку 57 (запись есть, файла нет)"""
    from app.models.document import Document
    
    # Создаем запись с несуществующим путем
    doc = Document(user_id=mock_client_profile.id, type="passport", file_path="media/non_existent.pdf")
    db_session.add(doc)
    await db_session.commit()

    response = await client.get(f"/documents/{doc.id}", headers=client_auth_headers)
    assert response.status_code == 404
    assert "Файл на диске отсутствует" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_document_forbidden(
    client: AsyncClient, 
    mock_client_profile,   # Тот, кто будет "злоумышленником"
    mock_landlord_profile, # Тот, кому принадлежит документ
    db_session
):
    """Один юзер пытается скачать документ другого юзера (ошибка 403)."""
    from app.models.document import Document
    from app.services.auth import AuthService

    # 1. Создаем документ для Лендлорда (Чужого для клиента юзера)
    doc = Document(
        user_id=mock_landlord_profile.id, 
        type="passport", 
        file_path="media/documents/secret.pdf"
    )
    db_session.add(doc)
    await db_session.commit()

    # 2. Генерируем токен для КЛИЕНТА (который не владеет этим документом)
    token = AuthService.create_access_token(data={"sub": str(mock_client_profile.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Клиент пытается скачать документ Лендлорда
    response = await client.get(f"/documents/{doc.id}", headers=headers)
    
    # 4. Проверяем, что доступ запрещен
    assert response.status_code == 403
    assert response.json()["detail"] == "Доступ запрещен к чужим документам"

