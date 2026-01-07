from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingRead, BookingUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=list[BookingRead])
def get_bookings(
    landlord_id: int | None = None,
    client_id: int | None = None,
    apartment_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[Booking]:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(booking_data: BookingCreate, db: Session = Depends(get_db)) -> Booking:
    """Create a new booking."""
    # Create a Range object from start_date and end_date
    # [) means: start_date is included, end_date is excluded (hotel standard)
    booking_period = Range(booking_data.start_date, booking_data.end_date, bounds="[)")

    booking = Booking(
        booking_period=booking_period,
        cost=booking_data.cost,
        booking_status=booking_data.booking_status.value,
        landlord_id=booking_data.landlord_id,
        client_id=booking_data.client_id,
        apartment_id=booking_data.apartment_id,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/{booking_id}", response_model=BookingRead)
def update_booking(
    booking_id: int, booking_data: BookingUpdate, db: Session = Depends(get_db)
) -> Booking:
    """Update a booking."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    update_data = booking_data.model_dump(exclude_unset=True)

    # Handle booking_status enum conversion
    if update_data.get("booking_status"):
        update_data["booking_status"] = update_data["booking_status"].value

    # Handle date updates - need to reconstruct the Range if either date is updated
    start_date = update_data.pop("start_date", None)
    end_date = update_data.pop("end_date", None)

    if start_date or end_date:
        # Get current dates from booking_period
        current_start = booking.booking_period.lower if booking.booking_period else None
        current_end = booking.booking_period.upper if booking.booking_period else None

        # Use new dates if provided, otherwise keep current
        new_start = start_date if start_date else current_start
        new_end = end_date if end_date else current_end

        # Create new Range with updated dates
        booking.booking_period = Range(new_start, new_end, bounds="[)")

    # Update remaining fields
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    db.delete(booking)
    db.commit()
