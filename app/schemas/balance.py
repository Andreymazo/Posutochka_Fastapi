from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class BalanceBase(BaseModel):
    """Base schema for Balance - common fields."""

    amount: float = Field(..., gt=0)


class BalanceCreate(BalanceBase):
    """Schema for creating a new Balance."""

    # Field(gt=0) заставит Pydantic выбрасывать ValidationError при значении 0 или меньше
    amount: Decimal = Field(gt=0, description="Сумма должна быть больше нуля")
    user_id: int

class BalanceUpdate(BaseModel):
    """Schema for updating a Balance - all fields optional."""

    amount: float | None = Field(None, gt=0)


class BalanceRead(BalanceBase):
    """Schema for reading Balance data (response)."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
