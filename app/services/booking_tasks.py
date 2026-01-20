from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Booking, Message, User, Apartment, Landlord
from app.services.telegram_service import TelegramService
from app.database import AsyncSessionLocal # Импортируем фабрику сессий
from sqlalchemy.orm import selectinload 


tg_service = TelegramService()

async def send_booking_notification(booking_id: int):
    """Фоновая задача для отправки уведомления арендодателю."""
    async with AsyncSessionLocal() as db:
        # 1. Получаем полные данные о бронировании
        result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.apartment))
            .where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        if not booking: return

        # 2. Ищем Telegram ID арендодателя
        user_res = await db.execute(
            select(User).join(Landlord).where(Landlord.id == booking.landlord_id)
        )
        landlord_user = user_res.scalars().first()

        if landlord_user and landlord_user.telegram_id:
            # 3. Отправляем реальное сообщение в Telegram
            text = f"🏠 Новая бронь!\nОбъект ID: {booking.apartment_id}\nСумма: {booking.cost}\n\nОтветьте на это сообщение для связи."
            
            tg_msg_id = await tg_service.send_message(
                tg_user_id=landlord_user.telegram_id,
                text=text
            )

            if tg_msg_id:
                # 4. Сохраняем ID сообщения в БД, чтобы работал Reply
                new_msg = Message(
                    text=text,
                    booking_id=booking.id,
                    sender_id=landlord_user.id,
                    tg_message_id=tg_msg_id,
                    is_read=True
                )
                db.add(new_msg)
                await db.commit()
                print(f"DEBUG: Фоновая задача выполнена. Сообщение {tg_msg_id} привязано к брони {booking_id}")
