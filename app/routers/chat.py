import os
from decimal import Decimal
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload # Добавлено для загрузки апартамента
from app.database import get_async_db
from app.models import Message, User, Booking, Client, CoinsTransaction
from app.services.telegram_service import TelegramService

router = APIRouter()
tg_service = TelegramService()

@router.post("/")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_async_db)):
    data = await request.json()
    print(f"DEBUG: Входящие данные: {data}") 

    if "message" in data:
        msg = data["message"]
        text = msg.get("text", "")
        tg_user_id = msg["from"]["id"]

        # Обработка /start
        if text == "/start":
            await tg_service.send_message(
                tg_user_id=tg_user_id, 
                text="Добро пожаловать в Посуточку! 🏠"
            )
            return {"status": "ok"}
   
        # Логика Reply (ответа)
        if "reply_to_message" in msg:
            original_tg_id = msg["reply_to_message"]["message_id"]

            # 1. Ищем оригинальное сообщение
            result = await db.execute(
                select(Message).where(Message.tg_message_id == original_tg_id)
            )
            original_msg = result.scalars().first()

            if original_msg:
                # 2. Ищем отправителя (Андрея/Охунжона)
                user_res = await db.execute(select(User).where(User.telegram_id == tg_user_id))
                sender = user_res.scalars().first()
        
                if sender:
                    # 3. Сохраняем новый ответ
                    new_message = Message(
                        text=text,
                        booking_id=original_msg.booking_id,
                        sender_id=sender.id,
                        tg_message_id=msg["message_id"],
                        is_read=False
                    )
                    db.add(new_message)

                    # 4. Обновляем статус брони и грузим апартамент сразу (selectinload)
                    booking_res = await db.execute(
                        select(Booking)
                        .where(Booking.id == original_msg.booking_id)
                        .options(selectinload(Booking.apartment)) 
                    )
                    booking = booking_res.scalar_one_or_none()

                    if booking:
                        confirm_words = ["подтверждаю", "ок", "одобряю", "да", "confirm"]
                        is_confirmed = any(word in text.lower() for word in confirm_words)
                        print(f"DEBUG: Условие 'confirmed' сработало для брони {booking.id}")
                        if is_confirmed:
                           # 1. Меняем статус
                            booking.booking_status = "confirmed"
                            print(f"DEBUG: Статус брони {booking.id} обновлен на confirmed")

                            # 2. НАЧИСЛЯЕМ COINS (Логика а-ля Суточно.ру)
                            # Допустим, кэшбэк 5% от стоимости брони
                            cashback = booking.cost * Decimal("0.05")
                            
                            # Создаем транзакцию
                            new_coin_tx = CoinsTransaction(
                                user_id=booking.client_id, # Получатель - гость
                                amount=cashback,
                                source_app="posutochka",
                                booking_id=booking.id,
                                description=f"Кэшбэк за бронирование #{booking.id}"
                            )
                            db.add(new_coin_tx)

                            # Обновляем баланс пользователя-клиента (Охунжона)
                            client_user.coins_balance += cashback 
                            
                            # Обновляем текст уведомления для клиента
                            notification_msg = (
                                f"✅ ПОДТВЕРЖДЕНО\n"
                                f"Арендодатель ответил: \"{text}\"\n"
                                f"💰 Вам начислено кэшбэком: {cashback} Coins!"
                            )
                            # 5. Уведомление клиента
                            client_user_res = await db.execute(
                                select(User).join(Client).where(Client.id == booking.client_id)
                            )
                            client_user = client_user_res.scalars().first()

                        if client_user and client_user.telegram_id:
                            status_label = "✅ ПОДТВЕРЖДЕНО" if is_confirmed else "📩 Новое сообщение"
                            apt_name = booking.apartment.name if booking.apartment else "Объект"
                            
                            notification_msg = (
                                f"{status_label}\n"
                                f"Арендодатель ответил: \"{text}\"\n"
                                f"Объект: {apt_name}"
                            )
                            
                            await tg_service.send_message(
                                tg_user_id=client_user.telegram_id, 
                                text=notification_msg
                            )

                    # ФИНАЛЬНЫЙ КОММИТ (Один для всего)
                    await db.commit()
                    print(f"DEBUG: Все изменения сохранены в БД")

    return {"status": "ok"}


# import os
# from fastapi import APIRouter, Request, Depends, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from app.database import get_async_db
# from app.models import Message, User, Booking
# from app.services.telegram_service import TelegramService

# router = APIRouter()

# tg_service = TelegramService()

# # Токен для минимальной проверки, что это пишет именно Телеграм (опционально)
# TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# @router.post("/")
# async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_async_db)):
#     """Принимает обновления от Telegram API."""
#     data = await request.json()
#      # ДОБАВЬТЕ ЭТО: теперь вы увидите в консоли всё, что прислал Телеграм
#     print(f"DEBUG: Входящие данные: {data}") 

#     if "message" in data and data["message"].get("text") == "/start":
#         tg_id = data["message"]["from"]["id"]
        
#         # Отправляем приветствие
#         await tg_service.send_message(
#             tg_user_id=tg_id, 
#             text="Добро пожаловать в Посуточку! 🏠\nВаш аккаунт привязан. Теперь вы будете получать уведомления о бронированиях здесь."
#         )
        
#         print(f"Пользователь {tg_id} успешно получил приветствие.")
#         return {"status": "ok"}
    
#     if "message" in data:
#         msg_text = data["message"].get("text")
#         print(f"DEBUG: Текст сообщения: {msg_text}")
        
#         if msg_text == "/start":
#             tg_id = data["message"]["from"]["id"]
#             print(f"Пользователь запустил бота. Его TG ID: {tg_id}")
#             return {"status": "ok"}
   
#     # Нас интересуют только сообщения, которые являются ответами (reply)
#     if "message" in data and "reply_to_message" in data["message"]:
#         msg = data["message"]
#         text = msg.get("text")
#         tg_user_id = msg["from"]["id"]
        
#         # ID сообщения, на которое ответил Арендодатель
#         original_tg_id = msg["reply_to_message"]["message_id"]

#         # 1. Ищем оригинальное сообщение в нашей БД по tg_message_id
#         result = await db.execute(
#             select(Message).where(Message.tg_message_id == original_tg_id)
#         )
#         # original_msg = result.scalar_one_or_none()
#         original_msg = result.scalars().first()

#         if original_msg:
#             # 2. Ищем нашего пользователя в БД по tg_user_id
#             user_result = await db.execute(
#                 select(User).where(User.telegram_id == tg_user_id)
#             )
#             # sender = user_result.scalar_one_or_none()
#             sender = user_result.scalars().first()
    
#             if sender:
#                 # 3. Сохраняем ответ в базу данных
#                 new_message = Message(
#                     text=text,
#                     booking_id=original_msg.booking_id,
#                     sender_id=sender.id,
#                     tg_message_id=msg["message_id"], # сохраняем ID уже этого ответа
#                     is_read=False
#                 )
#                 db.add(new_message)
#                 await db.commit()
                
#                 # Здесь можно добавить логику уведомления Клиента (через API или другого бота)
#                 print(f"Ответ сохранен для брони {original_msg.booking_id}: {text}")

#                 # 2. ДОБАВЛЯЕМ ЛОГИКУ ОБНОВЛЕНИЯ СТАТУСА БРОНИ
#                 # Ищем бронирование, к которому относится сообщение
#                 booking_result = await db.execute(
#                     select(Booking).where(Booking.id == original_msg.booking_id)
#                 )
#                 booking = booking_result.scalar_one_or_none()

#                 if booking:
#                     # 1. Логика изменения статуса (как мы и обсуждали)
#                     confirm_words = ["подтверждаю", "ок", "одобряю", "да", "confirm"]
#                     is_confirmed = any(word in text.lower() for word in confirm_words)
                    
#                     if is_confirmed:
#                         booking.booking_status = "confirmed"
                    
#                     await db.commit() # Сначала сохраняем статус в базе

#                     # 2. УВЕДОМЛЕНИЕ ВТОРОЙ СТОРОНЫ
#                     # Ищем клиента (Охунжона), чтобы отправить ему радостную новость
#                     # Мы берем client_id из бронирования и через него выходим на telegram_id
#                     client_user_result = await db.execute(
#                         select(User).join(Client).where(Client.id == booking.client_id)
#                     )
#                     client_user = client_user_result.scalars().first()

#                     if client_user and client_user.telegram_id:
#                         status_text = "✅ ПОДТВЕРЖДЕНО" if is_confirmed else "📩 Новое сообщение по вашей брони"
#                         notification_msg = (
#                             f"{status_text}\n"
#                             f"Арендодатель ответил: \"{text}\"\n"
#                             f"Объект: {booking.apartment.name}"
#                         )
                        
#                         # Отправляем через ваш сервис
#                         await tg_service.send_message(
#                             tg_user_id=client_user.telegram_id, 
#                             text=notification_msg
#                         )
#                         print(f"DEBUG: Уведомление отправлено пользователю {client_user.telegram_id}")


#     return {"status": "ok"}
