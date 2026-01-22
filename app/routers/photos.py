from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.photo import Photo
from app.schemas.photo import PhotoCreate, PhotoRead
import uuid
from pathlib import Path
import aiofiles

router = APIRouter(prefix="/photos", tags=["photos"])

# Путь для сохранения (совпадает с тем, что в main.py)
UPLOAD_DIR = Path("media/apartments")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=PhotoRead, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    apartment_id: int = Form(...),
    is_main: bool = Form(False),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db)
) -> Photo:
    """
    Загрузка файла на диск и создание записи в БД.
    Используем Form для метаданных, чтобы передать файл и ID объекта одновременно.
    """
    # 1. Валидация расширения
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Допустимы только изображения (jpg, png, webp)"
        )

    # 2. Генерация уникального пути
    file_name = f"{uuid.uuid4()}{ext}"
    relative_path = f"media/apartments/{file_name}"
    absolute_path = Path(relative_path)

    # 3. Асинхронная запись файла на диск
    async with aiofiles.open(absolute_path, "wb") as buffer:
        while content := await file.read(1024 * 1024):  # Читаем чанками
            await buffer.write(content)

    # 4. Логика единственного главного фото (is_main)
    if is_main:
        await db.execute(
            update(Photo)
            .where(Photo.apartment_id == apartment_id)
            .values(is_main=False)
        )

    # 5. Создание записи в базе
    new_photo = Photo(
        apartment_id=apartment_id,
        url=f"/{relative_path}", # Слэш в начале для корректной работы StaticFiles
        is_main=is_main
    )
    
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    return new_photo

@router.get("/", response_model=list[PhotoRead])
async def get_photos(
    apartment_id: int | None = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)
) -> list[Photo]:
    """Get all photos with optional apartment filter and pagination."""
    query = select(Photo)
    if apartment_id:
        query = query.filter(Photo.apartment_id == apartment_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{photo_id}", response_model=PhotoRead)
async def get_photo(photo_id: int, db: AsyncSession = Depends(get_async_db)) -> Photo:
    """Get a specific photo by ID."""
    query = select(Photo).filter(Photo.id == photo_id)
    result = await db.execute(query)
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.post("/", response_model=PhotoRead, status_code=status.HTTP_201_CREATED)
async def create_photo(photo_data: PhotoCreate, db: AsyncSession = Depends(get_async_db)) -> Photo:
    """Create a new photo."""
    photo = Photo(apartment_id=photo_data.apartment_id, url=photo_data.url)
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(photo_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a photo."""
    query = select(Photo).filter(Photo.id == photo_id)
    result = await db.execute(query)
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    await db.delete(photo)
    await db.commit()
