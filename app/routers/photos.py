from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.photo import Photo
from app.schemas.photo import PhotoCreate, PhotoRead

router = APIRouter(prefix="/photos", tags=["photos"])


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
