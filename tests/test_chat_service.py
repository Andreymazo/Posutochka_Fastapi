"""Tests for Chat Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.chat_service import ChatService
from app.models import Message, Booking, Landlord, User


@pytest.mark.asyncio
async def test_save_and_notify_success(db_session: AsyncSession, created_booking: Booking):
    """Тест успешного сохранения сообщения и отправки уведомления."""
    # Подготовка
    booking_id = created_booking.id
    sender_id = created_booking.client_id
    text = "Тестовое сообщение от клиента"

    # Устанавливаем telegram_id для арендодателя
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 123456789
    await db_session.commit()

    # Мокируем TelegramService
    with patch('app.services.chat_service.TelegramService.send_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = 999  # message_id в Telegram

        # Выполнение
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

        # Проверки
        assert result is not None
        assert result.text == text
        assert result.booking_id == booking_id
        assert result.sender_id == sender_id
        assert result.tg_message_id == 999

        # Проверяем, что send_message был вызван с правильными параметрами
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[1]['tg_user_id'] == 123456789
        assert f"Бронь #{booking_id}" in call_args[1]['text']
        assert text in call_args[1]['text']


@pytest.mark.asyncio
async def test_save_and_notify_no_telegram_id(db_session: AsyncSession, created_booking: Booking):
    """Тест сохранения сообщения когда у арендодателя нет telegram_id."""
    # Подготовка
    booking_id = created_booking.id
    sender_id = created_booking.client_id
    text = "Сообщение без telegram_id"

    # Убеждаемся, что telegram_id = None
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = None
    await db_session.commit()

    # Мокируем TelegramService (не должен быть вызван)
    with patch('app.services.chat_service.TelegramService.send_message', new_callable=AsyncMock) as mock_send:
        # Выполнение
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

        # Проверки
        assert result is not None
        assert result.text == text
        assert result.booking_id == booking_id
        assert result.sender_id == sender_id
        assert result.tg_message_id is None  # Не должно быть установлено

        # send_message НЕ должен быть вызван
        mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_save_and_notify_booking_not_found(db_session: AsyncSession, created_client):
    """Тест обработки случая, когда бронирование не найдено."""
    # Подготовка
    booking_id = 99999  # Несуществующий ID
    sender_id = created_client.id
    text = "Сообщение для несуществующей брони"

    # Мокируем TelegramService
    with patch('app.services.chat_service.TelegramService.send_message', new_callable=AsyncMock) as mock_send:
        # Выполнение
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

        # Проверки
        assert result is not None  # Сообщение всё равно сохранено
        assert result.text == text
        assert result.booking_id == booking_id
        assert result.sender_id == sender_id
        assert result.tg_message_id is None

        # send_message НЕ должен быть вызван (бронирование не найдено)
        mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_save_and_notify_telegram_service_fails(db_session: AsyncSession, created_booking: Booking):
    """Тест обработки ошибки отправки в Telegram."""
    # Подготовка
    booking_id = created_booking.id
    sender_id = created_booking.client_id
    text = "Сообщение с ошибкой отправки"

    # Устанавливаем telegram_id
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 123456789
    await db_session.commit()

    # Мокируем TelegramService с ошибкой (возвращает None)
    with patch('app.services.chat_service.TelegramService.send_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None  # Ошибка отправки

        # Выполнение
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

        # Проверки
        assert result is not None
        assert result.text == text
        assert result.tg_message_id is None  # Не установлено из-за ошибки

        # send_message был вызван, но вернул None
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_save_and_notify_with_html_text(db_session: AsyncSession, created_booking: Booking):
    """Тест отправки сообщения с HTML форматированием."""
    # Подготовка
    booking_id = created_booking.id
    sender_id = created_booking.client_id
    text = "<b>Жирный текст</b> и <i>курсив</i>"

    # Устанавливаем telegram_id
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 987654321
    await db_session.commit()

    # Мокируем TelegramService
    with patch('app.services.chat_service.TelegramService.send_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = 888

        # Выполнение
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

        # Проверки
        assert result is not None
        assert result.text == text
        assert result.tg_message_id == 888

        # Проверяем что HTML теги сохранились в тексте сообщения
        call_args = mock_send.call_args
        assert text in call_args[1]['text']


@pytest.mark.asyncio
async def test_save_and_notify_multiple_messages(db_session: AsyncSession, created_booking: Booking):
    """Тест отправки нескольких сообщений для одного бронирования."""
    # Подготовка
    booking_id = created_booking.id
    sender_id = created_booking.client_id

    # Устанавливаем telegram_id
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 111222333
    await db_session.commit()

    # Мокируем TelegramService
    with patch('app.services.chat_service.TelegramService.send_message', new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = [101, 102, 103]  # Разные message_id

        # Отправляем 3 сообщения
        messages = []
        for i in range(3):
            msg = await ChatService.save_and_notify(
                db_session, booking_id, sender_id, f"Сообщение {i+1}"
            )
            messages.append(msg)

        # Проверки
        assert len(messages) == 3
        assert messages[0].tg_message_id == 101
        assert messages[1].tg_message_id == 102
        assert messages[2].tg_message_id == 103
        assert mock_send.call_count == 3
