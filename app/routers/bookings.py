from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingRead, BookingUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=List[BookingRead])
def get_bookings(
    landlord_id: int = None,
    client_id: int = None,
    apartment_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Booking]:
    """Get all bookings with optional filters and pagination."""
    query = db.query(Booking)
    if landlord_id:
        query = query.filter(Booking.landlord_id == landlord_id)
    if client_id:
        query = query.filter(Booking.client_id == client_id)
    if apartment_id:
        query = query.filter(Booking.apartment_id == apartment_id)
    bookings = query.offset(skip).limit(limit).all()
    return bookings


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: int, db: Session = Depends(get_db)) -> Booking:
    """Get a specific booking by ID."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    return booking


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db)
) -> Booking:
    """Create a new booking."""
    booking = Booking(
        start_date=booking_data.start_date,
        end_date=booking_data.end_date,
        cost=booking_data.cost,
        booking_status=booking_data.booking_status.value,
        landlord_id=booking_data.landlord_id,
        client_id=booking_data.client_id,
        apartment_id=booking_data.apartment_id
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/{booking_id}", response_model=BookingRead)
def update_booking(
    booking_id: int,
    booking_data: BookingUpdate,
    db: Session = Depends(get_db)
) -> Booking:
    """Update a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    update_data = booking_data.model_dump(exclude_unset=True)
    if "booking_status" in update_data and update_data["booking_status"]:
        update_data["booking_status"] = update_data["booking_status"].value

    for field, value in update_data.items():
        setattr(booking, field, value)

    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    db.delete(booking)
    db.commit()
