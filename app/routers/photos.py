from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.photo import Photo
from app.schemas.photo import PhotoCreate, PhotoRead
import uuid
from pathlib import Path
import aiofiles
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.user import User

router = APIRouter(prefix="/photos", tags=["photos"])

# Путь для сохранения (совпадает с тем, что в main.py)
UPLOAD_DIR = Path("media/apartments")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
from app.services.roles import get_current_landlord  # Импортируем роль
from app.models.user import User
from app.models.apartment import Apartment # Нужно для проверки владения

@router.post("/upload", response_model=PhotoRead, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    apartment_id: int = Form(...),
    is_main: bool = Form(False),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    # 1. Защищаем эндпоинт ролью
    current_user: User = Depends(get_current_landlord) 
) -> Photo:
    
    # 2. ПРОВЕРКА ВЛАДЕНИЯ
    # Сначала проверяем, существует ли апартамент и принадлежит ли он юзеру
    stmt = select(Apartment).where(Apartment.id == apartment_id)
    result = await db.execute(stmt)
    apartment = result.scalar_one_or_none()

    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Апартамент не найден"
        )
    
    if apartment.landlord_id != current_user.landlord.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вы не можете загружать фото в чужой апартамент"
        )

    # 3. Валидация расширения (твой код)
    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Допустимы только изображения (jpg, png, webp)"
        )

    # 4. Сохранение файла (твой код с aiofiles)
    file_name = f"{uuid.uuid4()}{ext}"
    relative_path = f"media/apartments/{file_name}"
    absolute_path = Path(relative_path)

    async with aiofiles.open(absolute_path, "wb") as buffer:
        while content := await file.read(1024 * 1024):
            await buffer.write(content)

    # 5. Логика is_main и сохранение в базу (твой код)
    if is_main:
        await db.execute(
            update(Photo)
            .where(Photo.apartment_id == apartment_id)
            .values(is_main=False)
        )

    new_photo = Photo(
        apartment_id=apartment_id,
        url=f"/{relative_path}",
        is_main=is_main
    )
    
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    return new_photo

# Не забудь про DELETE — его тоже нужно защитить!
@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_landlord) # Только лендлорд
) -> None:
    # Ищем фото и подтягиваем апартамент, чтобы проверить владельца
    query = select(Photo).where(Photo.id == photo_id)
    result = await db.execute(query)
    photo = result.scalar_one_or_none()

    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Проверяем, что фото принадлежит апартаменту этого лендлорда
    # Для этого нужно, чтобы в модели Photo была связь или загрузить Apartment
    apt_result = await db.execute(select(Apartment).where(Apartment.id == photo.apartment_id))
    apartment = apt_result.scalar_one()
    
    if apartment.landlord_id != current_user.landlord.id:
        raise HTTPException(status_code=403, detail="Нельзя удалять чужие фото")

    # (Опционально) Удаление физического файла с диска
    # file_path = Path(photo.url.lstrip("/"))
    # if file_path.exists(): file_path.unlink()

    await db.delete(photo)
    await db.commit()


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
async def delete_photo(
    photo_id: int, 
    db: AsyncSession = Depends(get_async_db),
    # 1. Добавляем обязательную авторизацию лендлорда
    current_user: User = Depends(get_current_landlord)
) -> None:
    """Delete a photo with ownership check."""
    
    # 2. Ищем фото
    query = select(Photo).filter(Photo.id == photo_id)
    result = await db.execute(query)
    photo = result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    # 3. Ищем апартамент, чтобы проверить владельца
    # Используем selectinload или обычный select, чтобы найти связь
    from app.models.apartment import Apartment
    apt_query = select(Apartment).where(Apartment.id == photo.apartment_id)
    apt_result = await db.execute(apt_query)
    apartment = apt_result.scalar_one()

    # 4. ПРОВЕРКА ВЛАДЕНИЯ
    if apartment.landlord_id != current_user.landlord.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вы не можете удалять чужие фотографии"
        )

    # 5. Сама операция удаления
    await db.delete(photo)
    await db.commit()

