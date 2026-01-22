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


router = APIRouter(prefix="/documents", tags=["documents"])

DOCS_DIR = Path("media/documents")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    user_id: int = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        raise HTTPException(status_code=400, detail="Формат файла не поддерживается")

    file_name = f"doc_{user_id}_{uuid.uuid4().hex}{ext}"
    full_path = DOCS_DIR / file_name

    # Асинхронно пишем
    async with aiofiles.open(full_path, "wb") as buffer:
        while content := await file.read(1024 * 1024):
            await buffer.write(content)

    # Сохраняем в БД
    new_doc = Document(
        user_id=user_id,
        type=doc_type,
        file_path=str(full_path)
    )
    db.add(new_doc)
    await db.commit()
    return {"id": new_doc.id, "status": "uploaded"}
from fastapi.responses import FileResponse

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