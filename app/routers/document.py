import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.models.document import Document
from sqlalchemy import select
from app.services.auth import get_current_user
from app.models.user import User
from fastapi.responses import FileResponse
import magic

router = APIRouter(prefix="/documents", tags=["documents"])

DOCS_DIR = Path("media/documents")
DOCS_DIR.mkdir(parents=True, exist_ok=True)


async def validate_file_content(file: UploadFile, allowed_types: list[str]):
    # Читаем первые 2048 байт (этого достаточно для определения типа)
    head = await file.read(2048)
    await file.seek(0)  # Сбрасываем указатель в начало, чтобы потом сохранить файл целиком
    
    # Определяем MIME-тип
    mime = magic.from_buffer(head, mime=True)
    
    if mime not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимое содержимое файла. Ожидалось: {allowed_types}, получено: {mime}"
        )

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    # 1. Получаем юзера напрямую из токена
    current_user: User = Depends(get_current_user) 
):
    # Список разрешенных MIME-типов
    ALLOWED_MIME = ["application/pdf", "image/jpeg", "image/png"]
    # ПРОВЕРКА ПО СОДЕРЖИМОМУ
    await validate_file_content(file, ALLOWED_MIME)
    # Теперь мы НЕ верим user_id из формы, а используем current_user.id
    user_id = current_user.id

    # Валидация расширения
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        raise HTTPException(status_code=400, detail="Формат файла не поддерживается")

    # Путь (лучше использовать user_id из токена для папок)
    file_name = f"doc_{user_id}_{uuid.uuid4().hex}{ext}"
    full_path = DOCS_DIR / file_name

    # Запись... (твой код через aiofiles)

    # Сохраняем в БД
    new_doc = Document(
        user_id=user_id, # Гарантированно id владельца токена
        type=doc_type,
        file_path=str(full_path)
    )
    db.add(new_doc)
    await db.commit()
    return {"id": new_doc.id, "status": "uploaded"}


@router.get("/{doc_id}")
async def get_document(
    doc_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) # Теперь эндпоинт требует токен
):
    """Получение документа из БД и отдача файла."""
     # 1. Запрос в базу
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    
    # 2. Сначала проверяем существование (404)
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    # 3. ТВОЯ ПРОВЕРКА (403)
    # Позволяем доступ владельцу или Админу (если у тебя есть поле is_admin)
    if doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Доступ запрещен к чужим документам"
        )
    
    # 4. Проверка файла на диске и отдача
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл на диске отсутствует")

    return FileResponse(
        path=file_path, 
        filename=file_path.name,
        media_type='application/octet-stream'
    )