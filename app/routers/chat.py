import os
from decimal import Decimal
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload # Добавлено для загрузки апартамента
from app.database import get_async_db
from app.models import Message, User, Booking, Client, CoinsTransaction
from app.services.telegram_service import TelegramService
from app.core.redis import get_redis 

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

        # 1. ОБРАБОТКА /start (И обычный, и с UUID)
        if text.startswith("/start"):
            parts = text.split()
            
            # Если это просто /start (как в твоем тесте)
            if len(parts) == 1:
                await tg_service.send_message(tg_user_id=tg_user_id, text="Добро пожаловать! 🏠")
                return {"status": "ok"}
            
            # Если это /start с UUID (для подтверждения регистрации)
            link_token = parts[1]
            redis_client = await get_redis()
            user_id_bytes = await redis_client.get(f"tg_link:{link_token}")
            
            if user_id_bytes:
                user_id = int(user_id_bytes)
                user_res = await db.execute(select(User).where(User.id == user_id))
                user = user_res.scalar_one_or_none()
                
                if user:
                    user.telegram_id = tg_user_id
                    user.is_tg_verified = True
                    await db.commit()
                    await redis_client.delete(f"tg_link:{link_token}")
                    await redis_client.aclose()
                    await tg_service.send_message(
                        tg_user_id=tg_user_id, 
                        text=f"✅ Аккаунт {user.email} подтвержден!"
                    )
                    return {"status": "ok"}
            
            await redis_client.aclose()
            # Если токен не подошел, всё равно отвечаем "ok", чтобы Telegram не спамил повторами
            return {"status": "ok"}

        # 2. ОБРАБОТКА REPLY (Твоя рабочая логика)
        if "reply_to_message" in msg:
            original_tg_id = msg["reply_to_message"]["message_id"]
            # ... тут весь твой код без изменений до db.commit() ...
            result = await db.execute(select(Message).where(Message.tg_message_id == original_tg_id))
            original_msg = result.scalars().first()

            if original_msg:
                user_res = await db.execute(select(User).where(User.telegram_id == tg_user_id))
                sender = user_res.scalars().first()
        
                if sender:
                    new_message = Message(
                        text=text,
                        booking_id=original_msg.booking_id,
                        sender_id=sender.id,
                        tg_message_id=msg["message_id"],
                        is_read=False
                    )
                    db.add(new_message)

                    booking_res = await db.execute(
                        select(Booking)
                        .where(Booking.id == original_msg.booking_id)
                        .options(selectinload(Booking.apartment)) 
                    )
                    booking = booking_res.scalar_one_or_none()

                    if booking:
                        confirm_words = ["подтверждаю", "ок", "одобряю", "да", "confirm"]
                        is_confirmed = any(word in text.lower() for word in confirm_words)
                        
                        client_user_res = await db.execute(
                            select(User).join(Client, User.id == Client.user_id).where(Client.id == booking.client_id)
                        )
                        client_user = client_user_res.scalars().first()

                        if is_confirmed:
                            booking.booking_status = "confirmed"
                            if client_user:
                                cashback = booking.cost * Decimal("0.05")
                                new_coin_tx = CoinsTransaction(
                                    user_id=client_user.id,
                                    amount=cashback,
                                    source_app="posutochka",
                                    booking_id=booking.id,
                                    description=f"Кэшбэк за бронирование #{booking.id}"
                                )
                                db.add(new_coin_tx)
                                client_user.coins_balance += cashback 

                        if client_user and client_user.telegram_id:
                            status_label = "✅ ПОДТВЕРЖДЕНО" if is_confirmed else "📩 Новое сообщение"
                            apt_name = booking.apartment.name if booking.apartment else "Объект"
                            notification_msg = f"{status_label}\nАрендодатель ответил: \"{text}\"\n"
                            if is_confirmed:
                                notification_msg += f"💰 Вам начислено кэшбэком: {booking.cost * Decimal('0.05')} Coins!\n"
                            notification_msg += f"Объект: {apt_name}"
                            await tg_service.send_message(tg_user_id=client_user.telegram_id, text=notification_msg)

                    await db.commit()

    # Всегда возвращаем ok в конце
    return {"status": "ok"}

# from fastapi import Body
# @router.post("/")
# async def telegram_webhook(
#     request: Request, 
#     # Этот параметр нужен только для генерации документации Swagger
#     payload: dict = Body(..., example={
#         "message": {
#             "from": {"id": 12345678, "first_name": "Andrey"},
#             "text": "/start 984e4fcd-518e-4791-8e1d-8ac6ed380c0a"
#         }
#     }),
#     db: AsyncSession = Depends(get_async_db)
# ):
#     data = await request.json()
    
#     if "message" in data:
#             msg = data["message"]
#             text = msg.get("text", "")
#             tg_user_id = msg["from"]["id"]

#             # 1. ОБРАБОТКА КОМАНДЫ /start (Регистрация и приветствие)
#             if text.startswith("/start"):
#                 parts = text.split()
                
#                 # Если есть токен подтверждения (напр. /start uuid)
#                 if len(parts) > 1:
#                     link_token = parts[1]
#                     redis_client = await get_redis()
#                     user_id_bytes = await redis_client.get(f"tg_link:{link_token}")
                    
#                     if user_id_bytes:
#                         user_id = int(user_id_bytes)
#                         user_res = await db.execute(select(User).where(User.id == user_id))
#                         user = user_res.scalar_one_or_none()
                        
#                         if user:
#                             user.telegram_id = tg_user_id
#                             user.is_tg_verified = True
#                             await db.commit()
                            
#                             await redis_client.delete(f"tg_link:{link_token}")
#                             await redis_client.aclose()
                            
#                             await tg_service.send_message(
#                                 tg_user_id=tg_user_id, 
#                                 text=f"✅ Аккаунт {user.email} успешно подтвержден в Telegram!"
#                             )
#                             return {"status": "ok"}
                    
#                     await redis_client.aclose()
#                     await tg_service.send_message(tg_user_id=tg_user_id, text="❌ Ссылка устарела или неверна.")
#                     return {"status": "ok"}

#                 # Обычный /start без параметров
#                 await tg_service.send_message(tg_user_id=tg_user_id, text="Добро пожаловать! 🏠")
#                 return {"status": "ok"}


# @router.post("/")
# async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_async_db)):
#     data = await request.json()
#     print(f"DEBUG: Входящие данные: {data}") 

#     if "message" in data:
#         msg = data["message"]
#         text = msg.get("text", "")
#         tg_user_id = msg["from"]["id"]

#         if text == "/start":
#             await tg_service.send_message(tg_user_id=tg_user_id, text="Добро пожаловать! 🏠")
#             return {"status": "ok"}
   
#         if "reply_to_message" in msg:
#             original_tg_id = msg["reply_to_message"]["message_id"]

#             result = await db.execute(select(Message).where(Message.tg_message_id == original_tg_id))
#             original_msg = result.scalars().first()

#             if original_msg:
#                 user_res = await db.execute(select(User).where(User.telegram_id == tg_user_id))
#                 sender = user_res.scalars().first()
        
#                 if sender:
#                     new_message = Message(
#                         text=text,
#                         booking_id=original_msg.booking_id,
#                         sender_id=sender.id,
#                         tg_message_id=msg["message_id"],
#                         is_read=False
#                     )
#                     db.add(new_message)

#                     booking_res = await db.execute(
#                         select(Booking)
#                         .where(Booking.id == original_msg.booking_id)
#                         .options(selectinload(Booking.apartment)) 
#                     )
#                     booking = booking_res.scalar_one_or_none()

#                     if booking:
#                         confirm_words = ["подтверждаю", "ок", "одобряю", "да", "confirm"]
#                         is_confirmed = any(word in text.lower() for word in confirm_words)
                        
#                         # Сначала ищем клиента, чтобы он был доступен для начисления
#                         client_user_res = await db.execute(
#                             select(User).join(Client, User.id == Client.user_id).where(Client.id == booking.client_id)
#                         )
#                         client_user = client_user_res.scalars().first()

#                         if is_confirmed:
#                             booking.booking_status = "confirmed"

#                             if client_user:
#                                 cashback = booking.cost * Decimal("0.05")
                                
#                                 new_coin_tx = CoinsTransaction(
#                                     user_id=client_user.id, # Теперь client_user определен!
#                                     amount=cashback,
#                                     source_app="posutochka",
#                                     booking_id=booking.id,
#                                     description=f"Кэшбэк за бронирование #{booking.id}"
#                                 )
#                                 db.add(new_coin_tx)
#                                 client_user.coins_balance += cashback 

#                         # Отправка уведомления
#                         if client_user and client_user.telegram_id:
#                             status_label = "✅ ПОДТВЕРЖДЕНО" if is_confirmed else "📩 Новое сообщение"
#                             apt_name = booking.apartment.name if booking.apartment else "Объект"
                            
#                             notification_msg = (
#                                 f"{status_label}\n"
#                                 f"Арендодатель ответил: \"{text}\"\n"
#                             )
#                             if is_confirmed:
#                                 notification_msg += f"💰 Вам начислено кэшбэком: {booking.cost * Decimal('0.05')} Coins!\n"
                            
#                             notification_msg += f"Объект: {apt_name}"
                            
#                             await tg_service.send_message(
#                                 tg_user_id=client_user.telegram_id, 
#                                 text=notification_msg
#                             )

#                     await db.commit()

#     return {"status": "ok"}


# @router.post("/")
# async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_async_db)):
#     data = await request.json()
#     print(f"DEBUG: Входящие данные: {data}") 

#     if "message" in data:
#         msg = data["message"]
#         text = msg.get("text", "")
#         tg_user_id = msg["from"]["id"]

#         # Обработка /start
#         if text == "/start":
#             await tg_service.send_message(
#                 tg_user_id=tg_user_id, 
#                 text="Добро пожаловать в Посуточку! 🏠"
#             )
#             return {"status": "ok"}
   
#         # Логика Reply (ответа)
#         if "reply_to_message" in msg:
#             original_tg_id = msg["reply_to_message"]["message_id"]

#             # 1. Ищем оригинальное сообщение
#             result = await db.execute(
#                 select(Message).where(Message.tg_message_id == original_tg_id)
#             )
#             original_msg = result.scalars().first()

#             if original_msg:
#                 # 2. Ищем отправителя (Андрея/Охунжона)
#                 user_res = await db.execute(select(User).where(User.telegram_id == tg_user_id))
#                 sender = user_res.scalars().first()
        
#                 if sender:
#                     # 3. Сохраняем новый ответ
#                     new_message = Message(
#                         text=text,
#                         booking_id=original_msg.booking_id,
#                         sender_id=sender.id,
#                         tg_message_id=msg["message_id"],
#                         is_read=False
#                     )
#                     db.add(new_message)

#                     # 4. Обновляем статус брони и грузим апартамент сразу (selectinload)
#                     booking_res = await db.execute(
#                         select(Booking)
#                         .where(Booking.id == original_msg.booking_id)
#                         .options(selectinload(Booking.apartment)) 
#                     )
#                     booking = booking_res.scalar_one_or_none()

#                     if booking:
#                         confirm_words = ["подтверждаю", "ок", "одобряю", "да", "confirm"]
#                         is_confirmed = any(word in text.lower() for word in confirm_words)
#                         print(f"DEBUG: Условие 'confirmed' сработало для брони {booking.id}")
#                         if is_confirmed:
#                            # 1. Меняем статус
#                             booking.booking_status = "confirmed"
#                             print(f"DEBUG: Статус брони {booking.id} обновлен на confirmed")

#                             # 2. НАЧИСЛЯЕМ COINS (Логика а-ля Суточно.ру)
#                             # Допустим, кэшбэк 5% от стоимости брони
#                             cashback = booking.cost * Decimal("0.05")
                            
#                             # Создаем транзакцию
#                             new_coin_tx = CoinsTransaction(
#                                 user_id=booking.client_id, # Получатель - гость
#                                 amount=cashback,
#                                 source_app="posutochka",
#                                 booking_id=booking.id,
#                                 description=f"Кэшбэк за бронирование #{booking.id}"
#                             )
#                             db.add(new_coin_tx)

#                             # Обновляем баланс пользователя-клиента (Охунжона)
#                             client_user.coins_balance += cashback 
                            
#                             # Обновляем текст уведомления для клиента
#                             notification_msg = (
#                                 f"✅ ПОДТВЕРЖДЕНО\n"
#                                 f"Арендодатель ответил: \"{text}\"\n"
#                                 f"💰 Вам начислено кэшбэком: {cashback} Coins!"
#                             )
#                             # 5. Уведомление клиента
#                             client_user_res = await db.execute(
#                                 select(User).join(Client).where(Client.id == booking.client_id)
#                             )
#                             client_user = client_user_res.scalars().first()

#                         if client_user and client_user.telegram_id:
#                             status_label = "✅ ПОДТВЕРЖДЕНО" if is_confirmed else "📩 Новое сообщение"
#                             apt_name = booking.apartment.name if booking.apartment else "Объект"
                            
#                             notification_msg = (
#                                 f"{status_label}\n"
#                                 f"Арендодатель ответил: \"{text}\"\n"
#                                 f"Объект: {apt_name}"
#                             )
                            
#                             await tg_service.send_message(
#                                 tg_user_id=client_user.telegram_id, 
#                                 text=notification_msg
#                             )

#                     # ФИНАЛЬНЫЙ КОММИТ (Один для всего)
#                     await db.commit()
#                     print(f"DEBUG: Все изменения сохранены в БД")

#     return {"status": "ok"}


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
