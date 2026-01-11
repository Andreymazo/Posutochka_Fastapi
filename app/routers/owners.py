from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.owner import Owner
from app.schemas.owner import OwnerCreate, OwnerRead, OwnerUpdate

router = APIRouter(prefix="/owners", tags=["owners"])


@router.get("/", response_model=list[OwnerRead])
async def get_owners(
    user_id: int | None = None,
    booking_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
) -> list[Owner]:
    """Get all owners with optional user/booking filter and pagination."""
    query = select(Owner)
    if user_id:
        query = query.filter(Owner.user_id == user_id)
    if booking_id:
        query = query.filter(Owner.booking_id == booking_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{owner_id}", response_model=OwnerRead)
async def get_owner(owner_id: int, db: AsyncSession = Depends(get_async_db)) -> Owner:
    """Get a specific owner by ID."""
    query = select(Owner).filter(Owner.id == owner_id)
    result = await db.execute(query)
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
    return owner


@router.post("/", response_model=OwnerRead, status_code=status.HTTP_201_CREATED)
async def create_owner(owner_data: OwnerCreate, db: AsyncSession = Depends(get_async_db)) -> Owner:
    """Create a new owner."""
    owner = Owner(
        user_id=owner_data.user_id,
        booking_id=owner_data.booking_id,
        amount=owner_data.amount,
    )
    db.add(owner)
    await db.commit()
    await db.refresh(owner)
    return owner


@router.patch("/{owner_id}", response_model=OwnerRead)
async def update_owner(owner_id: int, owner_data: OwnerUpdate, db: AsyncSession = Depends(get_async_db)) -> Owner:
    """Update an owner."""
    query = select(Owner).filter(Owner.id == owner_id)
    result = await db.execute(query)
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    update_data = owner_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(owner, field, value)

    await db.commit()
    await db.refresh(owner)
    return owner


@router.delete("/{owner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_owner(owner_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete an owner."""
    query = select(Owner).filter(Owner.id == owner_id)
    result = await db.execute(query)
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    await db.delete(owner)
    await db.commit()
