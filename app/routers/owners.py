from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.owner import Owner
from app.schemas.owner import OwnerCreate, OwnerRead, OwnerUpdate

router = APIRouter(prefix="/owners", tags=["owners"])


@router.get("/", response_model=list[OwnerRead])
def get_owners(
    user_id: int | None = None,
    booking_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[Owner]:
    """Get all owners with optional user/booking filter and pagination."""
    query = db.query(Owner)
    if user_id:
        query = query.filter(Owner.user_id == user_id)
    if booking_id:
        query = query.filter(Owner.booking_id == booking_id)
    owners = query.offset(skip).limit(limit).all()
    return owners


@router.get("/{owner_id}", response_model=OwnerRead)
def get_owner(owner_id: int, db: Session = Depends(get_db)) -> Owner:
    """Get a specific owner by ID."""
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
    return owner


@router.post("/", response_model=OwnerRead, status_code=status.HTTP_201_CREATED)
def create_owner(owner_data: OwnerCreate, db: Session = Depends(get_db)) -> Owner:
    """Create a new owner."""
    owner = Owner(
        user_id=owner_data.user_id,
        booking_id=owner_data.booking_id,
        amount=owner_data.amount,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner


@router.patch("/{owner_id}", response_model=OwnerRead)
def update_owner(owner_id: int, owner_data: OwnerUpdate, db: Session = Depends(get_db)) -> Owner:
    """Update an owner."""
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    update_data = owner_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(owner, field, value)

    db.commit()
    db.refresh(owner)
    return owner


@router.delete("/{owner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner(owner_id: int, db: Session = Depends(get_db)) -> None:
    """Delete an owner."""
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    db.delete(owner)
    db.commit()
