"""Tests for Booking Tasks."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, Message, User
from app.services.booking_tasks import send_booking_notification


@pytest.mark.asyncio
async def test_send_booking_notification_success(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест успешной отправки уведомления о бронировании."""
    # Подготовка: устанавливаем telegram_id для арендодателя
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 123456789
    await db_session.commit()

    booking_id = created_booking.id

    # Мокируем TelegramService.send_message
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 777  # message_id в Telegram

        # Выполнение
        await send_booking_notification(booking_id)

        # Проверки отправки сообщения
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[1]["tg_user_id"] == 123456789
        assert "Новая бронь" in call_args[1]["text"]
        assert str(created_booking.apartment_id) in call_args[1]["text"]
        assert str(created_booking.cost) in call_args[1]["text"]

    # Проверяем, что сообщение сохранено в БД
    # Используем новую сессию для проверки (как в реальной фоновой задаче)
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as new_session:
        from sqlalchemy import select

        result = await new_session.execute(
            select(Message).where(Message.booking_id == booking_id, Message.tg_message_id == 777)
        )
        saved_message = result.scalar_one_or_none()

        assert saved_message is not None
        assert saved_message.booking_id == booking_id
        assert saved_message.tg_message_id == 777
        assert saved_message.is_read is True
        assert "Новая бронь" in saved_message.text


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
    """Тест обработки ошибки отправки в Telegram."""
    # Подготовка
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 987654321
    await db_session.commit()

    booking_id = created_booking.id

    # Мокируем TelegramService с ошибкой (возвращает None)
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = None  # Ошибка отправки

        # Выполнение
        await send_booking_notification(booking_id)

        # Проверка: send_message был вызван
        mock_send.assert_called_once()

    # Проверяем, что сообщение НЕ сохранено в БД (из-за проверки if tg_msg_id)
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as new_session:
        from sqlalchemy import select

        result = await new_session.execute(select(Message).where(Message.booking_id == booking_id))
        # Не должно быть новых сообщений, связанных с этим бронированием
        # (кроме возможных существующих)
        messages = result.scalars().all()
        # Проверяем, что нет сообщения с tg_message_id = None от этого теста
        assert not any(msg.tg_message_id is None and "Новая бронь" in msg.text for msg in messages)


@pytest.mark.asyncio
async def test_send_booking_notification_with_apartment_details(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест проверки включения деталей апартаментов в уведомление."""
    # Подготовка
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 555666777
    await db_session.commit()

    booking_id = created_booking.id

    # Мокируем TelegramService
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 888

        # Выполнение
        await send_booking_notification(booking_id)

        # Проверки содержимого сообщения
        call_args = mock_send.call_args
        message_text = call_args[1]["text"]

        assert "Новая бронь" in message_text
        assert f"Объект ID: {created_booking.apartment_id}" in message_text
        assert f"Сумма: {created_booking.cost}" in message_text
        assert "Ответьте на это сообщение" in message_text


@pytest.mark.asyncio
async def test_send_booking_notification_message_is_read_flag(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест проверки флага is_read для сохраненного сообщения."""
    # Подготовка
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 111222333
    await db_session.commit()

    booking_id = created_booking.id

    # Мокируем TelegramService
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 999

        # Выполнение
        await send_booking_notification(booking_id)

    # Проверяем флаг is_read
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as new_session:
        from sqlalchemy import select

        result = await new_session.execute(
            select(Message).where(Message.booking_id == booking_id, Message.tg_message_id == 999)
        )
        saved_message = result.scalar_one_or_none()

        assert saved_message is not None
        assert saved_message.is_read is True  # Должно быть True, как в коде


@pytest.mark.asyncio
async def test_send_booking_notification_sender_id_is_landlord(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест проверки, что sender_id сообщения - это ID пользователя арендодателя."""
    # Подготовка
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 444555666
    expected_sender_id = landlord_user.id
    await db_session.commit()

    booking_id = created_booking.id

    # Мокируем TelegramService
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 1111

        # Выполнение
        await send_booking_notification(booking_id)

    # Проверяем sender_id в сохраненном сообщении
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as new_session:
        from sqlalchemy import select

        result = await new_session.execute(
            select(Message).where(Message.booking_id == booking_id, Message.tg_message_id == 1111)
        )
        saved_message = result.scalar_one_or_none()

        assert saved_message is not None
        assert saved_message.sender_id == expected_sender_id


@pytest.mark.asyncio
async def test_send_booking_notification_uses_new_session(
    created_booking: Booking, db_session: AsyncSession
):
    """Тест проверки, что функция использует новую сессию AsyncSessionLocal."""
    # Подготовка
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 777888999
    await db_session.commit()

    booking_id = created_booking.id

    # Мокируем TelegramService и AsyncSessionLocal
    with patch(
        "app.services.booking_tasks.TelegramService.send_message", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 2222

        # Мокируем создание новой сессии для проверки, что используется AsyncSessionLocal
        with patch("app.services.booking_tasks.AsyncSessionLocal") as mock_session_factory:
            # Настраиваем мок так, чтобы он возвращал реальную сессию
            from app.database import AsyncSessionLocal as RealSessionLocal

            mock_session_factory.return_value.__aenter__.return_value = (
                await RealSessionLocal().__aenter__()
            )

            # Выполнение
            await send_booking_notification(booking_id)

            # Проверяем, что AsyncSessionLocal был вызван (новая сессия создана)
            mock_session_factory.assert_called_once()
