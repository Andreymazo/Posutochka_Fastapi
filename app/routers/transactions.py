from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=list[TransactionRead])
async def get_transactions(
    user_id: int | None = None,
    booking_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
) -> list[Transaction]:
    """Get all transactions with optional user/booking filter and pagination."""
    query = select(Transaction)
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if booking_id:
        query = query.filter(Transaction.booking_id == booking_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(transaction_id: int, db: AsyncSession = Depends(get_async_db)) -> Transaction:
    """Get a specific transaction by ID."""
    query = select(Transaction).filter(Transaction.id == transaction_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate, db: AsyncSession = Depends(get_async_db)
) -> Transaction:
    """Create a new transaction."""
    transaction = Transaction(
        user_id=transaction_data.user_id,
        booking_id=transaction_data.booking_id,
        balance_id=transaction_data.balance_id,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type.value,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    transaction_id: int, transaction_data: TransactionUpdate, db: AsyncSession = Depends(get_async_db)
) -> Transaction:
    """Update a transaction."""
    query = select(Transaction).filter(Transaction.id == transaction_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    update_data = transaction_data.model_dump(exclude_unset=True)
    if update_data.get("transaction_type"):
        update_data["transaction_type"] = update_data["transaction_type"].value

    for field, value in update_data.items():
        setattr(transaction, field, value)

    await db.commit()
    await db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(transaction_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a transaction."""
    query = select(Transaction).filter(Transaction.id == transaction_id)
    result = await db.execute(query)
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    await db.delete(transaction)
    await db.commit()
