from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.schemas.booking import BookingCreate, BookingRead, BookingUpdate
from app.services.booking_service import BookingService
from app.services.booking_tasks import send_booking_notification


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=list[BookingRead])
async def get_bookings(
    landlord_id: int | None = None,
    client_id: int | None = None,
    apartment_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
) -> list[BookingRead]:
    """Get all bookings with optional filters and pagination."""
    bookings = await BookingService.get_bookings(
        db=db,
        landlord_id=landlord_id,
        client_id=client_id,
        apartment_id=apartment_id,
        skip=skip,
        limit=limit,
    )
    return bookings


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_async_db)) -> BookingRead:
    """Get a specific booking by ID."""
    booking = await BookingService.get_booking_by_id(db=db, booking_id=booking_id)
    return booking


@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate, 
    background_tasks: BackgroundTasks, # Инжектируем сервис фоновых задач
    db: AsyncSession = Depends(get_async_db)
) -> BookingRead:
    """
    Create a new booking through business logic service.
    Validates against existing bookings and blocked periods.
    Checks minimum stay requirements.
    """
    # 1. Создаем бронь через ваш сервис (бизнес-логика остается нетронутой)
    new_booking = await BookingService.create_new_booking(
        db=db, booking_data=booking_data, client_id=booking_data.client_id
    )

    # 2. ЗАПУСКАЕМ «СИГНАЛ» (Фоновую задачу)
    # Передаем ID созданной брони. FastAPI выполнит это после возврата ответа.
    background_tasks.add_task(send_booking_notification, new_booking.id)

    return new_booking
# @router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
# async def create_booking(
#     booking_data: BookingCreate, db: AsyncSession = Depends(get_async_db)
# ) -> BookingRead:
#     """
#     Create a new booking through business logic service.
#     Validates against existing bookings and blocked periods.
#     Checks minimum stay requirements.
#     """
#     # Create booking using the service
#     # Service will check for date conflicts and minimum stay requirements
#     new_booking = await BookingService.create_new_booking(
#         db=db, booking_data=booking_data, client_id=booking_data.client_id
#     )
#     return new_booking


@router.patch("/{booking_id}", response_model=BookingRead)
async def update_booking(
    booking_id: int, booking_data: BookingUpdate, db: AsyncSession = Depends(get_async_db)
) -> BookingRead:
    """Update a booking."""
    booking = await BookingService.update_booking(
        db=db, booking_id=booking_id, booking_data=booking_data
    )
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(booking_id: int, db: AsyncSession = Depends(get_async_db)) -> None:
    """Delete a booking."""
    await BookingService.delete_booking(db=db, booking_id=booking_id)
