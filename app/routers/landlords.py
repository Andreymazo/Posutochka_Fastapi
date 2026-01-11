from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.landlord import Landlord
from app.schemas.landlord import LandlordCreate, LandlordRead, LandlordUpdate

router = APIRouter(prefix="/landlords", tags=["landlords"])


@router.get("/", response_model=list[LandlordRead])
async def get_landlords(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)) -> list[Landlord]:
    """Get all landlords with pagination."""
    query = select(Landlord).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{landlord_id}", response_model=LandlordRead)
async def get_landlord(landlord_id: int, db: AsyncSession = Depends(get_async_db)) -> Landlord:
    """Get a specific landlord by ID."""
    query = select(Landlord).filter(Landlord.id == landlord_id)
    result = await db.execute(query)
    landlord = result.scalar_one_or_none()
    if not landlord:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Landlord not found")
    return landlord


@router.post("/", response_model=LandlordRead, status_code=status.HTTP_201_CREATED)
async def create_landlord(landlord_data: LandlordCreate, db: AsyncSession = Depends(get_async_db)) -> Landlord:
    """Create a new landlord."""
    landlord = Landlord(
        user_id=landlord_data.user_id,
        first_name=landlord_data.first_name,
        last_name=landlord_data.last_name,
    )
    db.add(landlord)
    await db.commit()
    await db.refresh(landlord)
    return landlord


@router.patch("/{landlord_id}", response_model=LandlordRead)
async def update_landlord(
    landlord_id: int, landlord_data: LandlordUpdate, db: AsyncSession = Depends(get_async_db)
) -> Landlord:
    """Update a landlord."""
    query = select(Landlord).filter(Landlord.id == landlord_id)
    result = await db.execute(query)
    landlord = result.scalar_one_or_none()
    if not landlord:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Landlord not found")

    update_data = landlord_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(landlord, field, value)

    await db.commit()
    await db.refresh(landlord)
    return landlord


@router.delete("/{landlord_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_landlord(landlord_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a landlord."""
    query = select(Landlord).filter(Landlord.id == landlord_id)
    result = await db.execute(query)
    landlord = result.scalar_one_or_none()
    if not landlord:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Landlord not found")

    await db.delete(landlord)
    await db.commit()
