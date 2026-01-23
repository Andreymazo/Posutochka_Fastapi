import pytest
from httpx import AsyncClient
from io import BytesIO
import os


# Используем реальные байты PDF и JPG для тестов
# Байты настоящего PDF (минимальный)
REAL_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n"
# Байты настоящего JPG (минимальный)
REAL_JPG_BYTES = b'\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c\x20!\x21\x20\x20\x20\x13\x21\x23\x23\x23\x15\x2b\x2c\x2a\x30\x31\x30\x28\x31\x2f\x30\x30\x30\xff\xc4\x00\x1f\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xd9'

@pytest.mark.asyncio
async def test_upload_document_success(client: AsyncClient, mock_client_profile, client_auth_headers, db_session):
    """Тест загрузки документа: роутер сам берет ID из токена."""
    # Используем реальные байты PDF
    files = {"file": ("passport.pdf", BytesIO(REAL_PDF_BYTES), "application/pdf")}
    data = {"doc_type": "passport"}
    
    # Теперь в data только метаданные, БЕЗ user_id
    data = {
        "doc_type": "passport"
    }

    response = await client.post(
        "/documents/upload", 
        files=files, 
        data=data, 
        headers=client_auth_headers # ID возьмется отсюда
    )
    
    assert response.status_code == 201
    assert response.json()["status"] == "uploaded"
    
    # ПРОВЕРКА: Действительно ли в базе ID совпадает с владельцем токена?
    from app.models.document import Document
    from sqlalchemy import select
    
    doc_id = response.json()["id"]
    res = await db_session.execute(select(Document).where(Document.id == doc_id))
    db_doc = res.scalar_one()
    
    assert db_doc.user_id == mock_client_profile.id  # Это подтверждает, что подмена невозможна


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
     # Шлем реальный JPG, но под видом PDF
   # Отправляем простой текст. magic определит его как "text/plain"
    # А в ALLOWED_MIME у нас только pdf и картинки.
    files = {"file": ("danger.txt", BytesIO(b"just some plain text"), "text/plain")}
    data = {"doc_type": "passport"}
    
    response = await client.post("/documents/upload", files=files, data=data, headers=client_auth_headers)
    
    assert response.status_code == 400
    # Проверяем, что в тексте ошибки содержится правильный MIME-тип
    assert "image/jpeg" in response.json()["detail"] 
    assert "application/pdf" in response.json()["detail"]
    # response = await client.post("/documents/upload", files=files, data=data, headers=client_auth_headers)
    # assert response.status_code == 400
    # assert "Формат файла не поддерживается" in response.json()["detail"]

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

@pytest.mark.asyncio
async def test_upload_fake_pdf(client: AsyncClient, client_auth_headers):
    # Создаем файл с расширением .pdf, но внутри которого ОБЫЧНЫЙ ТЕКСТ
    files = {"file": ("fake.pdf", b"this is just plain text, not a PDF", "application/pdf")}
    data = {"doc_type": "passport"}
    
    response = await client.post("/documents/upload", files=files, data=data, headers=client_auth_headers)
    
    # Должно вернуть 400, так как содержимое не соответствует PDF
    assert response.status_code == 400
    assert "Недопустимое содержимое" in response.json()["detail"]

