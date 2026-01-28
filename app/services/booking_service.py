"""Booking service with business logic for creating and managing bookings."""
from fastapi import HTTPException, status
from sqlalchemy import and_, exists, func, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Apartment, ApartmentAvailability

# from app.models.apartmentavailability import ApartmentAvailability
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
        booking_period = Range(booking_data.check_in, booking_data.check_out, bounds="[)")
         # 1. Формируем два условия проверки занятости
        # Условие А: Есть ли перекрывающиеся активные брони
        booking_exists = select(Booking.id).where(
            and_(
                Booking.apartment_id == booking_data.apartment_id,
                Booking.booking_period.overlaps(booking_period),
                Booking.booking_status != "cancelled"
            )
        )

        # Условие Б: Есть ли перекрывающиеся блокировки от владельца
        availability_exists = select(ApartmentAvailability.id).where(
            and_(
                ApartmentAvailability.apartment_id == booking_data.apartment_id,
                ApartmentAvailability.blocked_period.overlaps(booking_period),
                ApartmentAvailability.is_blocked == True
            )
        )

        # Объединяем их через union_all и оборачиваем в exists()
        # Это исключает Cartesian Product и гарантирует правильный SQL
        busy_query = select(exists(booking_exists.union_all(availability_exists)))

        # 2. Выполняем проверку
        result = await db.execute(busy_query)
        is_busy = result.scalar()

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
        booking_days = (booking_data.check_out - booking_data.check_in).days

        # Check if booking meets minimum stay requirements
        for rule in availability_rules:
            if booking_days < rule.min_stay_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Минимальный срок проживания для выбранных дат: {rule.min_stay_days} дней",
                )
       # 4. Создаем объекты
              # --- ПОДГОТОВКА ДАННЫХ (вставляем перед пунктом 1) ---
        # Получаем объект апартамента из БД для получения актуальной цены и владельца
        apt_query = select(Apartment).where(Apartment.id == booking_data.apartment_id)
        apt_result = await db.execute(apt_query)
        apt = apt_result.scalar_one_or_none()

        if not apt:
            raise HTTPException(status_code=404, detail="Апартаменты не найдены")

        # Вычисляем количество дней и итоговую стоимость на стороне сервера
        booking_days = (booking_data.check_out - booking_data.check_in).days
        calculated_cost = apt.price_per_night * booking_days

        # ... (здесь идут твои проверки busy_query и min_stay_query) ...

        # --- ИСПРАВЛЕННЫЙ ПУНКТ 4 (Создание объекта) ---
        new_booking = Booking(
            booking_period=booking_period,
            cost=calculated_cost,            # Используем вычисленную сервером сумму
            booking_status="pending",        # Ставим начальный статус
            landlord_id=apt.landlord_id,     # Берем реального владельца из БД
            client_id=client_id,             # Получено из токена в роутере
            apartment_id=booking_data.apartment_id,
        )
        db.add(new_booking)


        # 5. Создаем блокировку
        availability_block = ApartmentAvailability(
            apartment_id=booking_data.apartment_id,
            blocked_period=booking_period,
            is_blocked=True
        )
        db.add(availability_block)

        # 6. Сначала выполняем flush, чтобы получить ID объектов, но не закрывать транзакцию
        await db.flush()
        
        # Сохраняем ID, чтобы не обращаться к объекту после коммита (избегаем селекта для refresh)
        booking_id = new_booking.id

        # 7. Фиксируем изменения
        await db.commit()

        # 8. Финальный запрос с использованием сохраненного ID
        # Это гарантирует, что мы начинаем новую чистую операцию в сессии
        final_query = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.payments),
                joinedload(Booking.apartment).selectinload(Apartment.availability_rules)
            )
        )
        
        result = await db.execute(final_query)
        # В 2026 году .unique() обязателен при использовании joinedload с коллекциями
        return result.unique().scalar_one()


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
            .options(
                selectinload(Booking.payments),
                # selectinload(Booking.apartment)  # Явно подгружаем апартамент
                # Явно загружаем апартамент И его правила, чтобы избежать Cartesian Product
                # selectinload(Booking.apartment).selectinload(Apartment.availability_rules)
                # Используем joinedload (JOIN), чтобы избежать Cartesian Product
                joinedload(Booking.apartment).selectinload(Apartment.availability_rules)
                )
        )
        result = await db.execute(query)
        # БЕЗ ЭТОГО МЕТОДА БУДЕТ ОШИБКА ИЛИ ПРЕДУПРЕЖДЕНИЕ
        booking = result.unique().scalar_one_or_none()
        # booking = result.scalar_one_or_none()

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
        query = select(Booking).options(selectinload(Booking.payments),
                selectinload(Booking.apartment).selectinload(Apartment.availability_rules))

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

    async def update_booking(
        db: AsyncSession, booking_id: int, booking_data: BookingUpdate
    ) -> Booking:
        booking = await BookingService.get_booking_by_id(db, booking_id)

        update_data = booking_data.model_dump(exclude_unset=True)

        # Handle booking_status enum conversion
        if update_data.get("booking_status"):
            update_data["booking_status"] = update_data["booking_status"].value

        # Handle date updates - need to reconstruct the Range if either date is updated
        check_in = update_data.pop("check_in", None)
        check_out = update_data.pop("check_out", None)

        if check_in or check_out:
            # Get current dates from booking_period
            current_start = booking.booking_period.lower if booking.booking_period else None
            current_end = booking.booking_period.upper if booking.booking_period else None

            # Use new dates if provided, otherwise keep current
            new_start = check_in if check_in else current_start
            new_end = check_out if check_out else current_end

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
