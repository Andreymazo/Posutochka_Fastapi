import os
from fastapi import APIRouter, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_async_db
from app.models import Message, User, Booking
from app.services.telegram_service import TelegramService

router = APIRouter()

tg_service = TelegramService()

# Токен для минимальной проверки, что это пишет именно Телеграм (опционально)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@router.post("")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Принимает обновления от Telegram API."""
    data = await request.json()
     # ДОБАВЬТЕ ЭТО: теперь вы увидите в консоли всё, что прислал Телеграм
    print(f"DEBUG: Входящие данные: {data}") 

    if "message" in data and data["message"].get("text") == "/start":
        tg_id = data["message"]["from"]["id"]
        
        # Отправляем приветствие
        await tg_service.send_message(
            chat_id=tg_id, 
            text="Добро пожаловать в Посуточку! 🏠\nВаш аккаунт привязан. Теперь вы будете получать уведомления о бронированиях здесь."
        )
        
        print(f"Пользователь {tg_id} успешно получил приветствие.")
        return {"status": "ok"}
    
    if "message" in data:
        msg_text = data["message"].get("text")
        print(f"DEBUG: Текст сообщения: {msg_text}")
        
        if msg_text == "/start":
            tg_id = data["message"]["from"]["id"]
            print(f"Пользователь запустил бота. Его TG ID: {tg_id}")
            return {"status": "ok"}
   
    # Нас интересуют только сообщения, которые являются ответами (reply)
    if "message" in data and "reply_to_message" in data["message"]:
        msg = data["message"]
        text = msg.get("text")
        tg_user_id = msg["from"]["id"]
        
        # ID сообщения, на которое ответил Арендодатель
        original_tg_id = msg["reply_to_message"]["message_id"]

        # 1. Ищем оригинальное сообщение в нашей БД по tg_message_id
        result = await db.execute(
            select(Message).where(Message.tg_message_id == original_tg_id)
        )
        # original_msg = result.scalar_one_or_none()
        original_msg = result.scalars().first()

        if original_msg:
            # 2. Ищем нашего пользователя в БД по tg_user_id
            user_result = await db.execute(
                select(User).where(User.telegram_id == tg_user_id)
            )
            # sender = user_result.scalar_one_or_none()
            sender = user_result.scalars().first()
    
            if sender:
                # 3. Сохраняем ответ в базу данных
                new_message = Message(
                    text=text,
                    booking_id=original_msg.booking_id,
                    sender_id=sender.id,
                    tg_message_id=msg["message_id"], # сохраняем ID уже этого ответа
                    is_read=False
                )
                db.add(new_message)
                await db.commit()
                
                # Здесь можно добавить логику уведомления Клиента (через API или другого бота)
                print(f"Ответ сохранен для брони {original_msg.booking_id}: {text}")

    return {"status": "ok"}
