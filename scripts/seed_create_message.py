import asyncio
import os
from datetime import datetime, UTC

# Импорт настроек и движка
from app.database import AsyncSessionLocal, async_engine
# Импорт моделей
from app.models import Message, User, Booking
from sqlalchemy import select

async def seed_test_message():
    # 1. НАСТРОЙКА ТЕСТОВЫХ ДАННЫХ
    # Возьмите REAL_TG_MESSAGE_ID из консоли (message_id любого вашего сообщения в боте)
    REAL_TG_MESSAGE_ID = 100  
    MY_TG_ID = 5015736552  # Ваш ID, который мы видели в консоли
    
    async with AsyncSessionLocal() as session:
        try:
            # Начинаем транзакцию через session.begin()
            async with session.begin():
                # 2. Ищем вашего пользователя, которого создал бот при нажатии /start
                result = await session.execute(
                    select(User).where(User.tg_user_id == MY_TG_ID)
                )
                user = result.scalar_one_or_none()

                if not user:
                    print(f"❌ Ошибка: Пользователь с TG ID {MY_TG_ID} не найден. Сначала напишите боту /start!")
                    return

                # 3. Ищем существующее бронирование (для foreign key)
                # Если в базе еще нет броней, для теста временно используем существующий ID или создаем заглушку
                booking_result = await session.execute(select(Booking).limit(1))
                booking = booking_result.scalar_one_or_none()
                
                if not booking:
                    print("⚠️ В базе нет ни одного бронирования. Убедитесь, что booking_id=1 существует.")
                    test_booking_id = 1 
                else:
                    test_booking_id = booking.id

                # 4. Создаем "оригинальное" сообщение, на которое мы будем отвечать Реплаем
                new_message = Message(
                    text="Тестовый вопрос от клиента: 'Можно ли заехать раньше 14:00?'",
                    booking_id=test_booking_id,
                    sender_id=user.id,
                    tg_message_id=REAL_TG_MESSAGE_ID, # Ключевое поле для поиска в webhook
                    is_read=True,
                    created_at=datetime.now(UTC)
                )
                
                session.add(new_message)
                # Flush не нужен, так как транзакция закроется (commit) в конце блока begin

            print(f"✅ Успех! Создано сообщение-заглушка (ID в TG: {REAL_TG_MESSAGE_ID}).")
            print(f"👉 Теперь в Telegram ответьте (Reply) на сообщение, ID которого вы указали.")

        except Exception as e:
            # Откат произойдет автоматически при ошибке внутри async with session.begin()
            print(f"❌ Ошибка при заполнении данных: {e}")
            raise
        finally:
            await session.close()

if __name__ == "__main__":
    try:
        asyncio.run(seed_test_message())
    finally:
        # Корректное закрытие пула соединений в 2026 году
        asyncio.run(async_engine.dispose())
