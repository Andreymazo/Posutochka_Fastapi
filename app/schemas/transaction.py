from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.transaction import TransactionType 

class TransactionBase(BaseModel):
    """Base schema for Transaction - common fields."""

    amount: float = Field(..., gt=0)
    transaction_type: TransactionType


class TransactionCreate(TransactionBase):
    """Schema for creating a new Transaction."""

    user_id: int
    booking_id: int
    balance_id: int


class TransactionUpdate(BaseModel):
    """Schema for updating a Transaction - all fields optional."""

    amount: float | None = Field(None, gt=0)
    transaction_type: TransactionType | None = None


class TransactionRead(TransactionBase):
    """Schema for reading Transaction data (response)."""

    id: int
    user_id: int
    booking_id: int
    balance_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
