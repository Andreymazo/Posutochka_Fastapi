from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=list[ReviewRead])
async def get_reviews(
    booking_id: int | None = None,
    landlord_id: int | None = None,
    client_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
) -> list[Review]:
    """Get all reviews with optional filters and pagination."""
    query = select(Review)
    if booking_id:
        query = query.filter(Review.booking_id == booking_id)
    if landlord_id:
        query = query.filter(Review.landlord_id == landlord_id)
    if client_id:
        query = query.filter(Review.client_id == client_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{review_id}", response_model=ReviewRead)
async def get_review(review_id: int, db: AsyncSession = Depends(get_async_db)) -> Review:
    """Get a specific review by ID."""
    query = select(Review).filter(Review.id == review_id)
    result = await db.execute(query)
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.post("/", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(review_data: ReviewCreate, db: AsyncSession = Depends(get_async_db)) -> Review:
    """Create a new review."""
    review = Review(
        booking_id=review_data.booking_id,
        landlord_id=review_data.landlord_id,
        client_id=review_data.client_id,
        rating=review_data.rating,
        review=review_data.review,
        author_role=review_data.author_role,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.patch("/{review_id}", response_model=ReviewRead)
async def update_review(
    review_id: int, review_data: ReviewUpdate, db: AsyncSession = Depends(get_async_db)
) -> Review:
    """Update a review."""
    query = select(Review).filter(Review.id == review_id)
    result = await db.execute(query)
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    update_data = review_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a review."""
    query = select(Review).filter(Review.id == review_id)
    result = await db.execute(query)
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    await db.delete(review)
    await db.commit()
