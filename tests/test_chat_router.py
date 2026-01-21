import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.models import Message, User, Booking, CoinsTransaction
from sqlalchemy import select

@pytest.mark.asyncio
async def test_webhook_start_command(client: AsyncClient):
    """Тест команды /start (покрывает ветку /start)."""
    payload = {
        "message": {
            "from": {"id": 12345},
            "text": "/start"
        }
    }
    with patch("app.routers.chat.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
        response = await client.post("/chat/", json=payload)
        assert response.status_code == 200
        mock_send.assert_called_once()

@pytest.mark.asyncio
async def test_webhook_reply_confirm_booking(
    client: AsyncClient, 
    db_session, 
    created_booking: Booking,
    created_landlord
):
    """Тест ответа 'подтверждаю' (покрывает самую длинную ветку: Coins, статус, уведомление)."""
    # 1. Подготовка: Создаем сообщение, на которое будем отвечать
    original_msg = Message(
        tg_message_id=777,
        booking_id=created_booking.id,
        text="Новая бронь",
        sender_id=created_booking.landlord.user_id
    )
    db_session.add(original_msg)
    
    # 2. Убеждаемся, что у арендодателя и клиента есть telegram_id
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 555
    
    client_user = await db_session.get(User, created_booking.client.user_id)
    client_user.telegram_id = 999
    
    await db_session.commit()

    # 3. Данные вебхука
    payload = {
        "message": {
            "message_id": 888,
            "from": {"id": 555}, # От арендодателя
            "text": "Ок, подтверждаю",
            "reply_to_message": {
                "message_id": 777 # Ответ на то самое сообщение
            }
        }
    }

    with patch("app.routers.chat.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
        response = await client.post("/chat/", json=payload)
        assert response.status_code == 200

        # Проверяем, что статус изменился
        await db_session.refresh(created_booking)
        assert created_booking.booking_status == "confirmed"

        # Проверяем начисление коинов
        res = await db_session.execute(select(CoinsTransaction).where(CoinsTransaction.booking_id == created_booking.id))
        assert res.scalars().first() is not None

        # Проверяем отправку уведомления клиенту
        mock_send.assert_called()
        assert "ПОДТВЕРЖДЕНО" in mock_send.call_args.kwargs["text"]
@pytest.mark.asyncio
async def test_webhook_reply_to_unknown_message(client: AsyncClient, db_session):
    """Тест ответа на сообщение, которого нет в нашей базе (ветка if not original_msg)."""
    payload = {
        "message": {
            "message_id": 999,
            "from": {"id": 555},
            "text": "Просто текст",
            "reply_to_message": {"message_id": 12345} # Этого ID нет в БД
        }
    }
    response = await client.post("/chat/", json=payload)
    assert response.status_code == 200
    # Код просто пропустит логику и вернет ok

@pytest.mark.asyncio
async def test_webhook_no_reply_no_start(client: AsyncClient):
    """Тест обычного сообщения без /start и без Reply (ветка выхода)."""
    payload = {
        "message": {
            "from": {"id": 555},
            "text": "Просто привет"
        }
    }
    response = await client.post("/chat/", json=payload)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_webhook_reply_to_non_existent_message(client: AsyncClient, db_session):
    """Закрывает ветку: 'if original_msg' (сообщение не найдено в нашей базе)."""
    payload = {
        "message": {
            "message_id": 999,
            "from": {"id": 555},
            "text": "Ответ в пустоту",
            "reply_to_message": {"message_id": 999999} # Несуществующий ID
        }
    }
    response = await client.post("/chat/", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_webhook_reply_from_unknown_user(client: AsyncClient, db_session, created_booking: Booking):
    """Закрывает ветку: 'if sender' (пользователь с таким TG ID не найден в базе)."""
    # 1. Подготовка: создаем сообщение, используя РЕАЛЬНЫЕ id из фикстуры
    msg = Message(
        tg_message_id=1000, 
        booking_id=created_booking.id, # Используем ID существующей брони
        text="test", 
        sender_id=created_booking.landlord.user_id # Используем ID существующего юзера
    )
    db_session.add(msg)
    await db_session.flush()

    # 2. Формируем вебхук от НЕИЗВЕСТНОГО пользователя (TG ID 888888 нет в базе)
    payload = {
        "message": {
            "message_id": 1001,
            "from": {"id": 888888}, # Этого TG ID нет в таблице User
            "text": "Я не из вашей базы",
            "reply_to_message": {"message_id": 1000}
        }
    }
    
    # 3. Выполнение
    response = await client.post("/chat/", json=payload)
    
    # 4. Проверка
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_no_message_key(client: AsyncClient):
    """Закрывает ветку: 'if "message" in data' (пришел вебхук без сообщения, например редактирование)."""
    payload = {"edited_message": {"text": "изменено"}}
    response = await client.post("/chat/", json=payload)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_webhook_reply_not_confirmed(client: AsyncClient, db_session, created_booking: Booking):
    """Закрывает ветку 'else' для подтверждения (is_confirmed = False)."""
    # 1. ПОДГОТОВКА
    # ВАЖНО: Меняем статус на pending, так как created_booking по умолчанию confirmed
    created_booking.booking_status = "pending"
    
    landlord = await db_session.get(User, created_booking.landlord.user_id)
    landlord.telegram_id = 555
    
    # Сохраняем изменения статуса в базе
    await db_session.flush()

    msg = Message(tg_message_id=2000, booking_id=created_booking.id, text="?", sender_id=landlord.id)
    db_session.add(msg)
    await db_session.flush()

    # 2. Текст без слов подтверждения
    payload = {
        "message": {
            "message_id": 2001,
            "from": {"id": 555},
            "text": "Просто уточняю детали", 
            "reply_to_message": {"message_id": 2000}
        }
    }

    # 3. ВЫПОЛНЕНИЕ
    response = await client.post("/chat/", json=payload)
    assert response.status_code == 200

    # 4. ПРОВЕРКА
    await db_session.refresh(created_booking)
    # Теперь статус должен остаться pending, а не стать confirmed
    assert created_booking.booking_status == "pending"
    assert created_booking.booking_status != "confirmed"


@pytest.mark.asyncio
async def test_webhook_reply_client_no_tg(client: AsyncClient, db_session, created_booking: Booking):
    """Закрывает ветку 'if client_user.telegram_id' (когда у гостя нет телеграма)."""
    landlord = await db_session.get(User, created_booking.landlord.user_id)
    landlord.telegram_id = 555
    
    # У клиента telegram_id = None
    client_user = await db_session.get(User, created_booking.client.user_id)
    client_user.telegram_id = None
    
    await db_session.flush()

    msg = Message(tg_message_id=3000, booking_id=created_booking.id, text="?", sender_id=landlord.id)
    db_session.add(msg)
    await db_session.flush()

    payload = {
        "message": {
            "message_id": 3001,
            "from": {"id": 555},
            "text": "Подтверждаю",
            "reply_to_message": {"message_id": 3000}
        }
    }

    with patch("app.routers.chat.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
        await client.post("/chat/", json=payload)
        # Уведомление не должно отправиться, так как у клиента нет TG
        mock_send.assert_not_called()

