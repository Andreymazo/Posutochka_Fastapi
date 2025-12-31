from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.apartment import Apartment
from app.schemas.apartment import ApartmentCreate, ApartmentRead, ApartmentUpdate

router = APIRouter(prefix="/apartments", tags=["apartments"])


@router.get("/", response_model=list[ApartmentRead])
def get_apartments(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[Apartment]:
    """Get all apartments with pagination."""
    apartments = db.query(Apartment).offset(skip).limit(limit).all()
    return apartments


@router.get("/{apartment_id}", response_model=ApartmentRead)
def get_apartment(apartment_id: int, db: Session = Depends(get_db)) -> Apartment:
    """Get a specific apartment by ID."""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")
    return apartment


@router.post("/", response_model=ApartmentRead, status_code=status.HTTP_201_CREATED)
def create_apartment(apartment_data: ApartmentCreate, db: Session = Depends(get_db)) -> Apartment:
    """Create a new apartment."""
    apartment = Apartment(
        name=apartment_data.name,
        description=apartment_data.description,
        price_per_night=apartment_data.price_per_night,
        address=apartment_data.address,
        location=apartment_data.location,
    )
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    return apartment


@router.patch("/{apartment_id}", response_model=ApartmentRead)
def update_apartment(
    apartment_id: int, apartment_data: ApartmentUpdate, db: Session = Depends(get_db)
) -> Apartment:
    """Update an apartment."""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")

    update_data = apartment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(apartment, field, value)

    db.commit()
    db.refresh(apartment)
    return apartment


@router.delete("/{apartment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_apartment(apartment_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an apartment."""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apartment not found")

    db.delete(apartment)
    db.commit()
