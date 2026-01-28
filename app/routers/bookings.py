from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.schemas.booking import BookingCreate, BookingRead, BookingUpdate
from app.services.booking_service import BookingService
from app.services.booking_tasks import send_booking_notification
# Импортируем наши новые сервисы бонусов
from app.services.coins_service import (
    process_landlord_booking_reward, 
    process_client_booking_bonus
)
from app.models import Landlord, Client, User, Booking, Payment
from app.services.auth import get_current_user
from fastapi import HTTPException, status
from app.schemas.booking import BookingStatus

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

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user) 
) -> BookingRead:
    
    # 1. Проверяем/Создаем клиента (уже обсудили)
    # Используем selectinload, чтобы избежать lazy loading у current_user
    res = await db.execute(select(Client).filter_by(user_id=current_user.id))
    client = res.scalar_one_or_none()
    if not client:
        client = Client(user_id=current_user.id)
        db.add(client)
        await db.flush()

   
    # 2. Создаем бронь через сервис
    # ВАЖНО: В сервисе или здесь установите статус 'confirmed', так как мы сразу "платим"
    new_booking = await BookingService.create_new_booking(
        db=db, 
        booking_data=booking_data, 
        client_id=client.id
    )
    new_booking.booking_status = BookingStatus.confirmed 

    # 3. Создаем запись о ПЛАТЕЖЕ (имитация списания)
    payment = Payment(
        booking_id=new_booking.id,
        amount=new_booking.cost,
        payment_status="paid", # Раз списали — значит paid
        payment_date=datetime.now()
    )
    db.add(payment)
    # Делаем flush, чтобы платеж привязался к сессии, но не коммитим пока всё
    await db.flush()

    # 4. ВНУТРЕННИЕ ТРАНЗАКЦИИ (Бонусы)
    # Эти функции внутри себя должны создавать записи в Transaction (wallet_transactions)
    landlord = await db.get(Landlord, new_booking.landlord_id)
    
    await process_landlord_booking_reward(
        landlord_id=landlord.user_id,
        total_price=float(new_booking.cost),
        booking_id=new_booking.id,
        db=db
    )

    await process_client_booking_bonus(
        client_id=current_user.id,
        total_price=float(new_booking.cost),
        booking_id=new_booking.id,
        db=db
    )

    # 5. Уведомления
    background_tasks.add_task(send_booking_notification, new_booking.id)

    # 6. КОММИТ И КОРРЕКТНЫЙ ВОЗВРАТ
    await db.commit()

    # Самый важный момент для устранения ошибки MissingGreenlet:
    # Перезагружаем бронь со ВСЕМИ связями, которые требует схема BookingRead
    final_query = (
        select(Booking)
        .options(
            selectinload(Booking.payments),     # Загружаем Payment
            #Dhtvtyyj pfrjvvtynbv lkz ntcnjd
            # selectinload(Booking.transactions)  # Загружаем Transaction (wallet_transactions)
        )
        .where(Booking.id == new_booking.id)
    )
    
    result = await db.execute(final_query)
    booking_ready_for_json = result.scalar_one()

    return booking_ready_for_json

# @router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
# async def create_booking(
#     booking_data: BookingCreate, 
#     background_tasks: BackgroundTasks,
#     db: AsyncSession = Depends(get_async_db),
#     current_user: User = Depends(get_current_user) 
# ) -> BookingRead:
#     """Создание бронирования с начислением бонусов обеим сторонам."""
#     # 0.1 Находим ID клиента, связанного с этим пользователем
#     # В твоей модели User есть связь 'client'
#     # 1. Безопасное получение Client ID
#     # Используем прямой запрос, чтобы избежать проблем с lazy loading
#     from sqlalchemy.orm import selectinload
#     from sqlalchemy import select
#     result = await db.execute(select(Client).filter_by(user_id=current_user.id))
#     client = result.scalar_one_or_none()

#     if not client:
#         client = Client(user_id=current_user.id)
#         db.add(client)
#         await db.flush()
#         # Теперь у client есть id благодаря flush()
    
#     target_client_id = client.id

#     # 2. Создание брони
#     # Убедитесь, что внутри create_new_booking не происходит еще одного commit, 
#     # иначе сессия может закрыться/сброситься
#     new_booking = await BookingService.create_new_booking(
#         db=db, booking_data=booking_data, client_id=target_client_id
#     )

#     if not new_booking:
#         raise HTTPException(status_code=400, detail="Ошибка создания бронирования")

#     # 3. Получаем Landlord (убедитесь, что landlord_id проставился в сервисе)
#     landlord = await db.get(Landlord, new_booking.landlord_id)
#     if not landlord:
#          raise HTTPException(status_code=404, detail="Арендодатель не найден")

#     # 4. Логика бонусов
#     await process_landlord_booking_reward(
#         landlord_id=landlord.user_id,
#         total_price=float(new_booking.cost),
#         booking_id=new_booking.id,
#         db=db
#     )
#     await process_client_booking_bonus(
#         client_id=current_user.id, # У нас уже есть user_id текущего юзера
#         total_price=float(new_booking.cost),
#         booking_id=new_booking.id,
#         db=db
#     )

#     # 5. Уведомления
#     background_tasks.add_task(send_booking_notification, new_booking.id)

#     await db.commit()
#      # Нам нужно заново подтянуть объект со всеми связями, 
#     # которые требуются в схеме BookingRead (например, payments, client и т.д.)
#     from sqlalchemy.orm import selectinload
#     from sqlalchemy import select

#     stmt = (
#         select(Booking)
#         .options(
#             selectinload(Booking.payments), # Подгружаем то, на чем споткнулся pydantic
#             # selectinload(Booking.client)   # Добавьте, если BookingRead требует данные клиента
#         )
#         .where(Booking.id == new_booking.id)
#     )
    
#     result = await db.execute(stmt)
#     booking_with_data = result.scalar_one()

#     return booking_with_data

#     # После коммита обновляем объект, чтобы вернуть его в response_model
#     await db.refresh(new_booking)

#     return new_booking

# __________________


    # if not current_user.client:
    #     # Если роли клиента нет, создаем её (на случай, если при регистрации не создалась)
        
    #     new_client = Client(user_id=current_user.id)
    #     db.add(new_client)
    #     await db.flush()
    
    # target_client_id = current_user.client.id
    # # 1. Создаем бронь (бизнес-логика валидации дат и т.д.)
    # new_booking = await BookingService.create_new_booking(
    #     db=db, booking_data=booking_data, client_id=target_client_id
    # )
    # # Получаем объект арендодателя, чтобы вытащить его user_id
    # landlord = await db.get(Landlord, new_booking.landlord_id)
    # # 2. Логика Арендодателя: 10% (списание + начисление сразу)
    # await process_landlord_booking_reward(
    #     landlord_id=landlord.user_id,  # ПЕРЕДАЕМ user_id, А НЕ landlord_id
    #     total_price=float(new_booking.cost),
    #     booking_id=new_booking.id,
    #     db=db
    # )
    # # Аналогично для клиента (если у него есть свой user_id)
    # client = await db.get(Client, new_booking.client_id)
    # # 3. Логика Клиента: 3% (создание транзакции + отложенная задача Celery на 30 дней)
    # await process_client_booking_bonus(
    #     client_id=client.user_id, # ПЕРЕДАЕМ user_id
    #     total_price=float(new_booking.cost),
    #     booking_id=new_booking.id,
    #     db=db
    # )

    # # 4. Уведомления (FastAPI BackgroundTasks)
    # background_tasks.add_task(send_booking_notification, new_booking.id)

    # # В 2026 году SQLAlchemy с AsyncSession требует явного коммита, 
    # # если он не сделан внутри сервиса
    # await db.commit()

    # return new_booking

# @router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
# async def create_booking(
#     booking_data: BookingCreate, 
#     background_tasks: BackgroundTasks, # Инжектируем сервис фоновых задач
#     db: AsyncSession = Depends(get_async_db)
# ) -> BookingRead:
#     """
#     Create a new booking through business logic service.
#     Validates against existing bookings and blocked periods.
#     Checks minimum stay requirements.
#     """
#     # 1. Создаем бронь через ваш сервис (бизнес-логика остается нетронутой)
#     new_booking = await BookingService.create_new_booking(
#         db=db, booking_data=booking_data, client_id=booking_data.client_id
#     )

#     # 2. ЗАПУСКАЕМ «СИГНАЛ» (Фоновую задачу)
#     # Передаем ID созданной брони. FastAPI выполнит это после возврата ответа.
#     background_tasks.add_task(send_booking_notification, new_booking.id)

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
