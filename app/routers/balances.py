from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.balance import Balance
from app.schemas.balance import BalanceCreate, BalanceRead, BalanceUpdate

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("/", response_model=list[BalanceRead])
def get_balances(
    user_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> list[Balance]:
    """Get all balances with optional user filter and pagination."""
    query = db.query(Balance)
    if user_id:
        query = query.filter(Balance.user_id == user_id)
    balances = query.offset(skip).limit(limit).all()
    return balances


@router.get("/{balance_id}", response_model=BalanceRead)
def get_balance(balance_id: int, db: Session = Depends(get_db)) -> Balance:
    """Get a specific balance by ID."""
    balance = db.query(Balance).filter(Balance.id == balance_id).first()
    if not balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance not found")
    return balance


@router.post("/", response_model=BalanceRead, status_code=status.HTTP_201_CREATED)
def create_balance(balance_data: BalanceCreate, db: Session = Depends(get_db)) -> Balance:
    """Create a new balance."""
    balance = Balance(
        user_id=balance_data.user_id,
        current_balance=balance_data.current_balance,
    )
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance


@router.patch("/{balance_id}", response_model=BalanceRead)
def update_balance(
    balance_id: int, balance_data: BalanceUpdate, db: Session = Depends(get_db)
) -> Balance:
    """Update a balance."""
    balance = db.query(Balance).filter(Balance.id == balance_id).first()
    if not balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance not found")

    update_data = balance_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(balance, field, value)

    db.commit()
    db.refresh(balance)
    return balance


@router.delete("/{balance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_balance(balance_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a balance."""
    balance = db.query(Balance).filter(Balance.id == balance_id).first()
    if not balance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Balance not found")

    db.delete(balance)
    db.commit()
