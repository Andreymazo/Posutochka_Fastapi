from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.landlord import Landlord
from app.schemas.landlord import LandlordCreate, LandlordRead, LandlordUpdate

router = APIRouter(prefix="/landlords", tags=["landlords"])


@router.get("/", response_model=List[LandlordRead])
def get_landlords(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Landlord]:
    """Get all landlords with pagination."""
    landlords = db.query(Landlord).offset(skip).limit(limit).all()
    return landlords


@router.get("/{landlord_id}", response_model=LandlordRead)
def get_landlord(landlord_id: int, db: Session = Depends(get_db)) -> Landlord:
    """Get a specific landlord by ID."""
    landlord = db.query(Landlord).filter(Landlord.id == landlord_id).first()
    if not landlord:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landlord not found"
        )
    return landlord


@router.post("/", response_model=LandlordRead, status_code=status.HTTP_201_CREATED)
def create_landlord(
    landlord_data: LandlordCreate,
    db: Session = Depends(get_db)
) -> Landlord:
    """Create a new landlord."""
    landlord = Landlord(
        user_id=landlord_data.user_id,
        first_name=landlord_data.first_name,
        last_name=landlord_data.last_name
    )
    db.add(landlord)
    db.commit()
    db.refresh(landlord)
    return landlord


@router.patch("/{landlord_id}", response_model=LandlordRead)
def update_landlord(
    landlord_id: int,
    landlord_data: LandlordUpdate,
    db: Session = Depends(get_db)
) -> Landlord:
    """Update a landlord."""
    landlord = db.query(Landlord).filter(Landlord.id == landlord_id).first()
    if not landlord:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landlord not found"
        )

    update_data = landlord_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(landlord, field, value)

    db.commit()
    db.refresh(landlord)
    return landlord


@router.delete("/{landlord_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_landlord(landlord_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a landlord."""
    landlord = db.query(Landlord).filter(Landlord.id == landlord_id).first()
    if not landlord:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Landlord not found"
        )

    db.delete(landlord)
    db.commit()
