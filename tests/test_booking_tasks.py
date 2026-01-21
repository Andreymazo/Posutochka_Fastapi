"""Tests for Booking Tasks."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, Message, User
from app.services.booking_tasks import send_booking_notification


@pytest.mark.asyncio
async def test_send_booking_notification_success(
    created_booking: Booking, 
    db_session: AsyncSession  # Используем ту самую сессию из conftest
):
    """Тест успешной отправки уведомления с подменой сессии."""
    
    # 1. Устанавливаем telegram_id (теперь это в рамках одной транзакции)
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 123456789
    await db_session.flush() # flush вместо commit, чтобы данные ушли в базу, но не закрыли транзакцию

    booking_id = created_booking.id

    # 2. Мокируем TelegramService
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 777

        # 3. ВАЖНО: Патчим AsyncSessionLocal внутри модуля задач!
        # Чтобы задача не создавала новую сессию, а использовала нашу
        with patch("app.services.booking_tasks.AsyncSessionLocal") as mock_session_local:
            # Настраиваем контекстный менеджер (async with AsyncSessionLocal() as session)
            mock_session_local.return_value.__aenter__.return_value = db_session

            # Выполнение
            await send_booking_notification(booking_id)

        # Проверки
        assert mock_send.called, "Метод send_message не был вызван! Проверьте, доходит ли код до отправки."
        mock_send.assert_called_once()
        
        call_args = mock_send.call_args
        assert call_args[1]["tg_user_id"] == 123456789
        assert "Новая бронь" in call_args[1]["text"]

    # 4. Проверка записи в БД (используем ту же db_session)
    from sqlalchemy import select
    result = await db_session.execute(
        select(Message).where(Message.booking_id == booking_id, Message.tg_message_id == 777)
    )
    saved_message = result.scalar_one_or_none()

    assert saved_message is not None
    assert saved_message.tg_message_id == 777
    assert saved_message.is_read is True

@pytest.mark.asyncio
async def test_send_booking_notification_no_booking(db_session: AsyncSession):
    """Тест обработки случая, когда бронирование не найдено."""
    # Используем несуществующий booking_id
    booking_id = 99999

    # Мокируем TelegramService
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        # Выполнение
        await send_booking_notification(booking_id)

        # Проверка: send_message НЕ должен быть вызван
        mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_send_booking_notification_no_telegram_id(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест обработки случая, когда у арендодателя нет telegram_id."""
    # Подготовка: убеждаемся, что telegram_id = None
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = None
    await db_session.commit()

    booking_id = created_booking.id

    # Мокируем TelegramService
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        # Выполнение
        await send_booking_notification(booking_id)

        # Проверка: send_message НЕ должен быть вызван
        mock_send.assert_not_called()
@pytest.mark.asyncio
async def test_send_booking_notification_telegram_fails(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест обработки ошибки отправки в Telegram (сервис вернул None)."""
    
    # 1. Подготовка: ставим telegram_id
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 987654321
    # Используем flush, чтобы изменения были видны в рамках одной транзакции
    await db_session.flush() 

    booking_id = created_booking.id

    # 2. Патчим TelegramService (имитируем ошибку) и AsyncSessionLocal (объединяем сессии)
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = None  # Имитация ошибки API Telegram

        with patch("app.services.booking_tasks.AsyncSessionLocal") as mock_session_local:
            # Заставляем задачу использовать нашу тестовую сессию db_session
            mock_session_local.return_value.__aenter__.return_value = db_session

            # Выполнение
            await send_booking_notification(booking_id)

        # Проверка: Попытка отправки была
        mock_send.assert_called_once()

    # 3. Проверяем, что сообщение НЕ сохранилось в БД
    from sqlalchemy import select
    from app.models import Message
    
    # Ищем любые сообщения для этой брони
    result = await db_session.execute(
        select(Message).where(Message.booking_id == booking_id)
    )
    messages = result.scalars().all()
    
    # Проверяем, что нет сообщения, которое мы только что пытались отправить
    # (если сервис вернул None, запись в базу Message произойти не должна)
    assert not any("Новая бронь" in msg.text for msg in messages), \
        "Сообщение сохранилось в БД, хотя Telegram вернул ошибку (None)"



@pytest.mark.asyncio
async def test_send_booking_notification_with_apartment_details(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест проверки включения деталей апартаментов в уведомление."""
    # Подготовка
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 555666777
    # Используем flush, чтобы данные были видны внутри транзакции
    await db_session.flush()

    booking_id = created_booking.id
    # 2. Мокируем отправку и ПАТЧИМ сессию
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 888

        # Подменяем AsyncSessionLocal, чтобы задача видела наши изменения в User
        with patch("app.services.booking_tasks.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session

            # Выполнение
            await send_booking_notification(booking_id)

        # 3. Проверки
        assert mock_send.called, "Метод send_message не был вызван! Проверьте патч сессии."
        
        call_args = mock_send.call_args
        message_text = call_args[1]["text"]

        assert "Новая бронь" in message_text
        assert f"Объект ID: {created_booking.apartment_id}" in message_text
        assert f"Сумма: {created_booking.cost}" in message_text
        # Если вы используете f-строки или форматирование float, 
        # проверьте точность (например, 1000.0 или 1000)
        assert "Ответьте на это сообщение" in message_text
 

@pytest.mark.asyncio
async def test_send_booking_notification_message_is_read_flag(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест проверки флага is_read для сохраненного сообщения."""
    # 1. Подготовка: ставим telegram_id
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 111222333
    
    # Используем flush, чтобы изменения были видны внутри транзакции теста
    await db_session.flush()

    booking_id = created_booking.id

    # 2. Мокируем TelegramService и ПАТЧИМ сессию внутри задачи
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 999

        # Подменяем AsyncSessionLocal на нашу db_session
        with patch("app.services.booking_tasks.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session

            # Выполнение
            await send_booking_notification(booking_id)

    # 3. Проверяем флаг is_read (используем ту же db_session)
    from sqlalchemy import select
    from app.models import Message

    result = await db_session.execute(
        select(Message).where(Message.booking_id == booking_id, Message.tg_message_id == 999)
    )
    saved_message = result.scalar_one_or_none()

    assert saved_message is not None, "Сообщение не было сохранено в БД"
    assert saved_message.is_read is True  # Проверяем логику: уведомление считается прочитанным при отправке



@pytest.mark.asyncio
async def test_send_booking_notification_sender_id_is_landlord(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест проверки, что sender_id сообщения - это ID пользователя арендодателя."""
    # 1. Подготовка
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 444555666
    expected_sender_id = landlord_user.id
    await db_session.flush() # Используем flush для видимости в транзакции

    booking_id = created_booking.id

    # 2. Мокируем Telegram и ПАТЧИМ сессию
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 1111

        with patch("app.services.booking_tasks.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = db_session

            # Выполнение
            await send_booking_notification(booking_id)

    # 3. Проверяем sender_id через нашу сессию
    from sqlalchemy import select
    result = await db_session.execute(
        select(Message).where(Message.booking_id == booking_id, Message.tg_message_id == 1111)
    )
    saved_message = result.scalar_one_or_none()

    assert saved_message is not None
    assert saved_message.sender_id == expected_sender_id
@pytest.mark.asyncio
async def test_send_booking_notification_uses_new_session(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест проверки, что функция вызывает AsyncSessionLocal."""
    # 1. Подготовка
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 777888999
    await db_session.flush()

    booking_id = created_booking.id

    # 2. Мокируем всё
    with patch("app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = 2222

        # Патчим фабрику сессий
        with patch("app.services.booking_tasks.AsyncSessionLocal") as mock_session_factory:
            # Нам нужно, чтобы мок вел себя как сессия и возвращал данные.
            # Мы подсовываем db_session, но следим за вызовом самой фабрики.
            mock_session_factory.return_value.__aenter__.return_value = db_session

            # Выполнение
            await send_booking_notification(booking_id)

            # Проверка 1: Сама фабрика была вызвана (значит код хотел новую сессию)
            mock_session_factory.assert_called_once()
            
            # Проверка 2: Сообщение реально ушло (значит сессия работала)
            assert mock_send.called
