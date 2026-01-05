from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=list[ReviewRead])
def get_reviews(
    booking_id: int | None = None,
    landlord_id: int | None = None,
    client_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[Review]:
    """Get all reviews with optional filters and pagination."""
    query = db.query(Review)
    if booking_id:
        query = query.filter(Review.booking_id == booking_id)
    if landlord_id:
        query = query.filter(Review.landlord_id == landlord_id)
    if client_id:
        query = query.filter(Review.client_id == client_id)
    reviews = query.offset(skip).limit(limit).all()
    return reviews


@router.get("/{review_id}", response_model=ReviewRead)
def get_review(review_id: int, db: Session = Depends(get_db)) -> Review:
    """Get a specific review by ID."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.post("/", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(review_data: ReviewCreate, db: Session = Depends(get_db)) -> Review:
    """Create a new review."""
    review = Review(
        booking_id=review_data.booking_id,
        landlord_id=review_data.landlord_id,
        client_id=review_data.client_id,
        rating=review_data.rating,
        review=review_data.review,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.patch("/{review_id}", response_model=ReviewRead)
def update_review(
    review_id: int, review_data: ReviewUpdate, db: Session = Depends(get_db)
) -> Review:
    """Update a review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    update_data = review_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    db.delete(review)
    db.commit()
