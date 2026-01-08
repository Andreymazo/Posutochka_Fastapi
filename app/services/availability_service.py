"""Availability service for managing apartment availability and blocking periods."""

from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.apartmentavailability import ApartmentAvailability


class AvailabilityService:
    """Service class for apartment availability management."""

    @staticmethod
    async def create_blocked_period(
        db: AsyncSession,
        apartment_id: int,
        start_date: date,
        end_date: date,
        reason: str | None = None,
        is_blocked: bool = True,
        custom_price: Decimal | None = None,
        min_stay_days: int = 1,
    ) -> ApartmentAvailability:
        """
        Create a blocked period or availability rule for an apartment.

        Args:
            db: Async database session
            apartment_id: ID of the apartment
            start_date: Start date of the period
            end_date: End date of the period
            reason: Reason for blocking (e.g., "Ремонт", "Личное использование")
            is_blocked: Whether the period is blocked for booking
            custom_price: Custom price for the period (for holidays, etc.)
            min_stay_days: Minimum stay requirement in days

        Returns:
            Created ApartmentAvailability object

        Raises:
            HTTPException: If overlapping availability rule exists
        """
        blocked_period = Range(start_date, end_date, bounds="[)")

        # Check for overlapping availability rules
        # Note: The database has an ExcludeConstraint that will also prevent this,
        # but we check here to provide a better error message
        overlap_query = select(ApartmentAvailability).where(
            and_(
                ApartmentAvailability.apartment_id == apartment_id,
                ApartmentAvailability.blocked_period.overlaps(blocked_period),
            )
        )

        result = await db.execute(overlap_query)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пересекающееся правило доступности уже существует для этого периода",
            )

        # Create the availability rule
        availability = ApartmentAvailability(
            apartment_id=apartment_id,
            blocked_period=blocked_period,
            reason=reason,
            is_blocked=is_blocked,
            custom_price=custom_price,
            min_stay_days=min_stay_days,
        )

        db.add(availability)
        await db.commit()
        await db.refresh(availability)
        return availability

    @staticmethod
    async def get_availability_rules(
        db: AsyncSession, apartment_id: int, skip: int = 0, limit: int = 100
    ) -> list[ApartmentAvailability]:
        """
        Get all availability rules for an apartment.

        Args:
            db: Async database session
            apartment_id: ID of the apartment
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of availability rules
        """
        query = (
            select(ApartmentAvailability)
            .where(ApartmentAvailability.apartment_id == apartment_id)
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_availability_rule_by_id(
        db: AsyncSession, rule_id: int
    ) -> ApartmentAvailability:
        """
        Get an availability rule by ID.

        Args:
            db: Async database session
            rule_id: ID of the availability rule

        Returns:
            ApartmentAvailability object

        Raises:
            HTTPException: If rule not found
        """
        query = select(ApartmentAvailability).where(ApartmentAvailability.id == rule_id)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability rule not found",
            )

        return rule

    @staticmethod
    async def update_availability_rule(
        db: AsyncSession,
        rule_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        reason: str | None = None,
        is_blocked: bool | None = None,
        custom_price: Decimal | None = None,
        min_stay_days: int | None = None,
    ) -> ApartmentAvailability:
        """
        Update an availability rule.

        Args:
            db: Async database session
            rule_id: ID of the rule to update
            start_date: New start date (optional)
            end_date: New end date (optional)
            reason: New reason (optional)
            is_blocked: New blocked status (optional)
            custom_price: New custom price (optional)
            min_stay_days: New minimum stay requirement (optional)

        Returns:
            Updated ApartmentAvailability object

        Raises:
            HTTPException: If rule not found
        """
        rule = await AvailabilityService.get_availability_rule_by_id(db, rule_id)

        # Update blocked_period if dates are provided
        if start_date or end_date:
            current_start = rule.blocked_period.lower if rule.blocked_period else None
            current_end = rule.blocked_period.upper if rule.blocked_period else None

            new_start = start_date if start_date else current_start
            new_end = end_date if end_date else current_end

            rule.blocked_period = Range(new_start, new_end, bounds="[)")

        # Update other fields if provided
        if reason is not None:
            rule.reason = reason
        if is_blocked is not None:
            rule.is_blocked = is_blocked
        if custom_price is not None:
            rule.custom_price = custom_price
        if min_stay_days is not None:
            rule.min_stay_days = min_stay_days

        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def delete_availability_rule(db: AsyncSession, rule_id: int) -> None:
        """
        Delete an availability rule.

        Args:
            db: Async database session
            rule_id: ID of the rule to delete

        Raises:
            HTTPException: If rule not found
        """
        rule = await AvailabilityService.get_availability_rule_by_id(db, rule_id)
        await db.delete(rule)
        await db.commit()
