from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.photo import Photo
from app.schemas.photo import PhotoCreate, PhotoRead

router = APIRouter(prefix="/photos", tags=["photos"])


@router.get("/", response_model=list[PhotoRead])
def get_photos(
    apartment_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[Photo]:
    """Get all photos with optional apartment filter and pagination."""
    query = db.query(Photo)
    if apartment_id:
        query = query.filter(Photo.apartment_id == apartment_id)
    photos = query.offset(skip).limit(limit).all()
    return photos


@router.get("/{photo_id}", response_model=PhotoRead)
def get_photo(photo_id: int, db: Session = Depends(get_db)) -> Photo:
    """Get a specific photo by ID."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.post("/", response_model=PhotoRead, status_code=status.HTTP_201_CREATED)
def create_photo(photo_data: PhotoCreate, db: Session = Depends(get_db)) -> Photo:
    """Create a new photo."""
    photo = Photo(apartment_id=photo_data.apartment_id, url=photo_data.url)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a photo."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    db.delete(photo)
    db.commit()
