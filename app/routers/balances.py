from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.balance import Balance
from app.schemas.balance import BalanceCreate, BalanceRead, BalanceUpdate

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("/", response_model=list[BalanceRead])
async def get_balances(
    user_id: int | None = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)
) -> list[Balance]:
    """Get all balances with optional user filter and pagination."""
    query = select(Balance)
    if user_id:
        query = query.filter(Balance.user_id == user_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{balance_id}", response_model=BalanceRead)
async def get_balance(balance_id: int, db: AsyncSession = Depends(get_async_db)) -> Balance:
    """Get a specific balance by ID."""
    query = select(Balance).filter(Balance.id == balance_id)
    result = await db.execute(query)
    balance = result.scalar_one_or_none()
    if not balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance not found")
    return balance


@router.post("/", response_model=BalanceRead, status_code=status.HTTP_201_CREATED)
async def create_balance(balance_data: BalanceCreate, db: AsyncSession = Depends(get_async_db)) -> Balance:
    """Create a new balance."""
    balance = Balance(
        user_id=balance_data.user_id,
        current_balance=balance_data.current_balance,
    )
    db.add(balance)
    await db.commit()
    await db.refresh(balance)
    return balance


@router.patch("/{balance_id}", response_model=BalanceRead)
async def update_balance(
    balance_id: int, balance_data: BalanceUpdate, db: AsyncSession = Depends(get_async_db)
) -> Balance:
    """Update a balance."""
    query = select(Balance).filter(Balance.id == balance_id)
    result = await db.execute(query)
    balance = result.scalar_one_or_none()
    if not balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance not found")

    update_data = balance_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(balance, field, value)

    await db.commit()
    await db.refresh(balance)
    return balance


@router.delete("/{balance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_balance(balance_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a balance."""
    query = select(Balance).filter(Balance.id == balance_id)
    result = await db.execute(query)
    balance = result.scalar_one_or_none()
    if not balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance not found")

    await db.delete(balance)
    await db.commit()
