from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/", response_model=list[PaymentRead])
async def get_payments(
    booking_id: int | None = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)
) -> list[Payment]:
    """Get all payments with optional booking filter and pagination."""
    query = select(Payment)
    if booking_id:
        query = query.filter(Payment.booking_id == booking_id)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_async_db)) -> Payment:
    """Get a specific payment by ID."""
    query = select(Payment).filter(Payment.id == payment_id)
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(payment_data: PaymentCreate, db: AsyncSession = Depends(get_async_db)) -> Payment:
    """Create a new payment."""
    payment = Payment(
        booking_id=payment_data.booking_id,
        amount=payment_data.amount,
        payment_status=payment_data.payment_status.value,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.patch("/{payment_id}", response_model=PaymentRead)
async def update_payment(
    payment_id: int, payment_data: PaymentUpdate, db: AsyncSession = Depends(get_async_db)
) -> Payment:
    """Update a payment."""
    query = select(Payment).filter(Payment.id == payment_id)
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    update_data = payment_data.model_dump(exclude_unset=True)
    if update_data.get("payment_status"):
        update_data["payment_status"] = update_data["payment_status"].value

    for field, value in update_data.items():
        setattr(payment, field, value)

    await db.commit()
    await db.refresh(payment)
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(payment_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a payment."""
    query = select(Payment).filter(Payment.id == payment_id)
    result = await db.execute(query)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    await db.delete(payment)
    await db.commit()
