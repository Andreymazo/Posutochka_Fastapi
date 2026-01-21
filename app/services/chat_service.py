from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Message, Booking, User, Landlord  # Импортируем Landlord
from app.services.telegram_service import TelegramService

class ChatService:
    @staticmethod
    async def save_and_notify(db: AsyncSession, booking_id: int, sender_id: int, text: str):
        # 1. Сохраняем в базу новое сообщение
        new_msg = Message(
            booking_id=booking_id,
            sender_id=sender_id,
            text=text
        )
        db.add(new_msg)
        await db.flush() 

        # 2. Ищем данные о брони и арендодателе
        # Исправлено: цепочка загрузки теперь идет через атрибуты моделей
        result = await db.execute(
            select(Booking)
            .options(
                selectinload(Booking.landlord).selectinload(Landlord.user)
            )
            .where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()

        # 3. Если нашли лендлорда и у него заполнен telegram_id — отправляем уведомление
        # ВАЖНО: убедитесь, что в модели User поле называется именно telegram_id
        if booking and booking.landlord.user.telegram_id:
            tg_msg_id = await TelegramService.send_message(
                tg_user_id=booking.landlord.user.telegram_id,
                text=f"<b>Новое сообщение (Бронь #{booking_id}):</b>\n{text}"
            )
            # Сохраняем ID сообщения из Телеграма для будущих ответов (Reply)
            if tg_msg_id:
                new_msg.tg_message_id = tg_msg_id
                new_msg.is_read = True  # Считаем прочитанным, так как оно ушло в ТГ
        
        await db.commit()
        return new_msg
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from sqlalchemy.orm import selectinload
# from app.models import Message, Booking, User
# from app.services.telegram_service import TelegramService

# class ChatService:
#     @staticmethod
#     async def save_and_notify(db: AsyncSession, booking_id: int, sender_id: int, text: str):
#         # 1. Сохраняем в базу
#         new_msg = Message(
#             booking_id=booking_id,
#             sender_id=sender_id,
#             text=text
#         )
#         db.add(new_msg)
#         await db.flush() # Получаем ID сообщения

#         # 2. Ищем, кому отправить (Landlord)
#         # В 2026 году используем асинхронный select с подгрузкой связей
#         result = await db.execute(
#             select(Booking)
#             .options(selectinload(Booking.landlord).selectinload(User))
#             .where(Booking.id == booking_id)
#         )
#         booking = result.scalar_one_or_none()

#         # 3. Если нашли лендлорда и у него есть TG — шлем
#         if booking and booking.landlord.user.tg_user_id:
#             tg_msg_id = await TelegramService.send_message(
#                 tg_user_id=booking.landlord.user.tg_user_id,
#                 text=f"<b>Новое сообщение (Бронь #{booking_id}):</b>\n{text}"
#             )
#             new_msg.tg_message_id = tg_msg_id
        
#         await db.commit()
#         return new_msg
