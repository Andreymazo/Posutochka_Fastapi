"""Router for apartment availability management."""

from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.schemas.availability import AvailabilityCreate, AvailabilityRead, AvailabilityUpdate
from app.services.availability_service import AvailabilityService

router = APIRouter(prefix="/availability", tags=["availability"])


@router.post("/", response_model=AvailabilityRead, status_code=status.HTTP_201_CREATED)
async def create_availability_rule(
    rule_data: AvailabilityCreate, db: AsyncSession = Depends(get_async_db)
) -> AvailabilityRead:
    """
    Create a new availability rule for an apartment.
    Landlords can use this to block dates or set custom prices and minimum stay requirements.
    """
    rule = await AvailabilityService.create_blocked_period(
        db=db,
        apartment_id=rule_data.apartment_id,
        start_date=rule_data.start_date,
        end_date=rule_data.end_date,
        reason=rule_data.reason,
        is_blocked=rule_data.is_blocked,
        custom_price=Decimal(str(rule_data.custom_price)) if rule_data.custom_price else None,
        min_stay_days=rule_data.min_stay_days,
    )
    return rule


@router.get("/apartment/{apartment_id}", response_model=list[AvailabilityRead])
async def get_apartment_availability_rules(
    apartment_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)
) -> list[AvailabilityRead]:
    """Get all availability rules for a specific apartment."""
    rules = await AvailabilityService.get_availability_rules(
        db=db, apartment_id=apartment_id, skip=skip, limit=limit
    )
    return rules


@router.get("/{rule_id}", response_model=AvailabilityRead)
async def get_availability_rule(
    rule_id: int, db: AsyncSession = Depends(get_async_db)
) -> AvailabilityRead:
    """Get a specific availability rule by ID."""
    rule = await AvailabilityService.get_availability_rule_by_id(db=db, rule_id=rule_id)
    return rule


@router.patch("/{rule_id}", response_model=AvailabilityRead)
async def update_availability_rule(
    rule_id: int, rule_data: AvailabilityUpdate, db: AsyncSession = Depends(get_async_db)
) -> AvailabilityRead:
    """Update an availability rule."""
    rule = await AvailabilityService.update_availability_rule(
        db=db,
        rule_id=rule_id,
        start_date=rule_data.start_date,
        end_date=rule_data.end_date,
        reason=rule_data.reason,
        is_blocked=rule_data.is_blocked,
        custom_price=Decimal(str(rule_data.custom_price)) if rule_data.custom_price else None,
        min_stay_days=rule_data.min_stay_days,
    )
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_availability_rule(
    rule_id: int, db: AsyncSession = Depends(get_async_db)
) -> None:
    """Delete an availability rule."""
    await AvailabilityService.delete_availability_rule(db=db, rule_id=rule_id)
