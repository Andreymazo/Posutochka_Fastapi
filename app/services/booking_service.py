"""Booking service with business logic for creating and managing bookings."""
from sqlalchemy import select, exists, or_, and_
from sqlalchemy import func 
from fastapi import HTTPException, status
from sqlalchemy import and_, exists, or_, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.apartmentavailability import ApartmentAvailability
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingUpdate


class BookingService:
    """Service class for booking business logic."""

    @staticmethod
    async def create_new_booking(
        db: AsyncSession, booking_data: BookingCreate, client_id: int
    ) -> Booking:
        """
        Create a new booking with validation against existing bookings and blocked periods.

        Args:
            db: Async database session
            booking_data: Booking creation data
            client_id: ID of the client creating the booking

        Returns:
            Created booking object

        Raises:
            HTTPException: If dates are already booked or unavailable
        """
        # Create Range object from start_date and end_date
        booking_period = Range(booking_data.start_date, booking_data.end_date, bounds="[)")

        # 1. Build query to check if dates are available
        busy_query = select(
            exists().where(
                or_(
                    # Check among active bookings
                    and_(
                        Booking.apartment_id == booking_data.apartment_id,
                        Booking.booking_period.overlaps(booking_period),
                        Booking.booking_status != "cancelled",
                    ),
                    # Check among landlord blocks (where booking is forbidden)
                    and_(
                        ApartmentAvailability.apartment_id == booking_data.apartment_id,
                        ApartmentAvailability.blocked_period.overlaps(booking_period),
                        ApartmentAvailability.is_blocked == True,  # noqa: E712
                    ),
                )
            )
        )

        # 2. Execute the check
        result = await db.execute(busy_query)
        is_busy = result.scalar()

        if is_busy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Выбранные даты уже заняты или недоступны",
            )

        # 3. Check minimum stay requirement for the period
        min_stay_query = select(ApartmentAvailability).where(
            and_(
                ApartmentAvailability.apartment_id == booking_data.apartment_id,
                ApartmentAvailability.blocked_period.overlaps(booking_period),
                ApartmentAvailability.min_stay_days > 1,
            )
        )

        result = await db.execute(min_stay_query)
        availability_rules = result.scalars().all()

        # Calculate booking duration
        booking_days = (booking_data.end_date - booking_data.start_date).days

        # Check if booking meets minimum stay requirements
        for rule in availability_rules:
            if booking_days < rule.min_stay_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Минимальный срок проживания для выбранных дат: {rule.min_stay_days} дней",
                )

        # 4. If available - create the booking object
        new_booking = Booking(
            booking_period=booking_period,
            cost=booking_data.cost,
            booking_status=booking_data.booking_status.value,
            landlord_id=booking_data.landlord_id,
            client_id=client_id,
            apartment_id=booking_data.apartment_id,
        )

        db.add(new_booking)
        await db.commit()
        await db.refresh(new_booking, ["payments"])
        return new_booking
# _______________________________________
# ======================================================== warnings summary ========================================================
# tests/test_bookings.py::TestBookingDateRange::test_create_booking_with_daterange
#   sys:1: SAWarning: SELECT statement has a cartesian product between FROM element(s) "apartment_availability" and FROM element "booking".  Apply join condition(s) between each element to resolve.

# -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
# Думаю…
# Предупреждение
# Cartesian Product возникает из-за того, что в одном запросе select вы используете обе модели (Booking и ApartmentAvailability) без условия JOIN. SQLAlchemy видит это и предупреждает, что база данных пытается перемножить все строки одной таблицы на все строки другой, что фатально для производительности.
# В 2026 году для решения этой проблемы в асинхронном FastAPI приложении лучше всего разделить проверку на два независимых подзапроса.
# Вот исправленный код для app/services/booking_service.py, который уберет это предупреждение:
# Исправленный create_new_booking
# python

# from sqlalchemy import select, exists, or_, and_
# # ... остальные импорты

# class BookingService:
#     @staticmethod
#     async def create_new_booking(db: AsyncSession, booking_data: BookingCreate, client_id: int):
        
#         # 1. Проверка пересечения с существующими бронями
#         booking_conflict = exists().where(
#             and_(
#                 Booking.apartment_id == booking_data.apartment_id,
#                 Booking.booking_period.overlaps(booking_data.booking_period),
#                 Booking.booking_status != "cancelled"
#             )
#         )

#         # 2. Проверка пересечения с блокировками арендодателя
#         availability_conflict = exists().where(
#             and_(
#                 ApartmentAvailability.apartment_id == booking_data.apartment_id,
#                 ApartmentAvailability.blocked_period.overlaps(booking_data.booking_period),
#                 ApartmentAvailability.is_blocked == True
#             )
#         )

#         # 3. Объединяем их в один запрос, не создавая Cartesian Product
#         # Используем select(exists(...).or_(exists(...))) или два отдельных scalar
#         query = select(or_(booking_conflict, availability_conflict))
        
#         is_busy = await db.scalar(query)

#         if is_busy:
#             raise HTTPException(
#                 status_code=400, 
#                 detail="Выбранные даты уже заняты или недоступны"
#             )

#         # ... дальше создание брони ...
#         new_booking = Booking(
#             **booking_data.model_dump(exclude={"booking_period"}), # Исключаем, если в схеме это не Range
#             booking_period=booking_data.booking_period,
#             client_id=client_id,
#             booking_status="pending"
#         )
#         # ...

# Используйте код с осторожностью.
# Почему это решает проблему:

#     Независимые exists: Когда мы оборачиваем каждую проверку в свой exists(), SQLAlchemy генерирует два подзапроса. Они не смешиваются в основном блоке FROM, и декартово произведение не возникает.
#     Безопасность: Мы проверяем is_blocked == True, что позволяет арендодателю менять цены через ApartmentAvailability, не блокируя при этом возможность бронирования (если is_blocked=False).

# Что проверить в тестах:
# Если предупреждение остается, проверьте, нет ли в тесте test_create_booking_with_daterange момента, где вы случайно делаете db.execute(select(Booking, ApartmentAvailability)). Запрос всегда должен быть направлен на конкретную модель или через четкий join.
# После замены на предложенную структуру с or_(booking_conflict, availability_conflict), предупреждение SAWarning исчезнет. [1, 2]
# _______________________________________



    @staticmethod
    async def get_booking_by_id(db: AsyncSession, booking_id: int) -> Booking:
        """
        Get a booking by ID.

        Args:
            db: Async database session
            booking_id: ID of the booking

        Returns:
            Booking object

        Raises:
            HTTPException: If booking not found
        """
        query = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.payments))
        )
        result = await db.execute(query)
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
            )

        return booking

    @staticmethod
    async def get_bookings(
        db: AsyncSession,
        landlord_id: int | None = None,
        client_id: int | None = None,
        apartment_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Booking]:
        """
        Get all bookings with optional filters and pagination.

        Args:
            db: Async database session
            landlord_id: Optional filter by landlord ID
            client_id: Optional filter by client ID
            apartment_id: Optional filter by apartment ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of bookings
        """
        # 1. Базовый запрос с подгрузкой платежей
        query = select(Booking).options(selectinload(Booking.payments))
        
        # 2. Фильтры
        if landlord_id:
            query = query.where(Booking.landlord_id == landlord_id)
        if client_id:
            query = query.where(Booking.client_id == client_id)
        if apartment_id:
            query = query.where(Booking.apartment_id == apartment_id)
        
        # 3. Сортировка (сначала самые свежие брони по дате заезда)
        # .lower() извлекает дату начала из диапазона
        query = query.order_by(func.lower(Booking.booking_period).desc())
        # 4. Пагинация
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_booking(
        db: AsyncSession, booking_id: int, booking_data: BookingUpdate
    ) -> Booking:
        """
        Update a booking.

        Args:
            db: Async database session
            booking_id: ID of the booking to update
            booking_data: Updated booking data

        Returns:
            Updated booking object

        Raises:
            HTTPException: If booking not found
        """
        # Get existing booking
        booking = await BookingService.get_booking_by_id(db, booking_id)

        update_data = booking_data.model_dump(exclude_unset=True)

        # Handle booking_status enum conversion
        if update_data.get("booking_status"):
            update_data["booking_status"] = update_data["booking_status"].value

        # Handle date updates - need to reconstruct the Range if either date is updated
        start_date = update_data.pop("start_date", None)
        end_date = update_data.pop("end_date", None)

        if start_date or end_date:
            # Get current dates from booking_period
            current_start = booking.booking_period.lower if booking.booking_period else None
            current_end = booking.booking_period.upper if booking.booking_period else None

            # Use new dates if provided, otherwise keep current
            new_start = start_date if start_date else current_start
            new_end = end_date if end_date else current_end

            # Create new Range with updated dates
            booking.booking_period = Range(new_start, new_end, bounds="[)")

        # Update remaining fields
        for field, value in update_data.items():
            setattr(booking, field, value)

        await db.commit()
        await db.refresh(booking, ["payments"])
        return booking

    @staticmethod
    async def delete_booking(db: AsyncSession, booking_id: int) -> None:
        """
        Delete a booking.

        Args:
            db: Async database session
            booking_id: ID of the booking to delete

        Raises:
            HTTPException: If booking not found
        """
        booking = await BookingService.get_booking_by_id(db, booking_id)
        await db.delete(booking)
        await db.commit()
