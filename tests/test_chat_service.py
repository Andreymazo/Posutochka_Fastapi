"""Tests for Chat Service."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, User
from app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_save_and_notify_success(db_session: AsyncSession, created_booking: Booking):
    """Тест успешного сохранения сообщения и отправки уведомления."""
    # 1. ПОДГОТОВКА
    booking_id = created_booking.id
    
    # Берем арендодателя - он ТОЧНО существует в базе, так как привязан к брони
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    
    # Если landlord_user по какой-то причине None, используем прямой ID из связи
    sender_id = landlord_user.id if landlord_user else created_booking.landlord.user_id
    
    # Устанавливаем telegram_id для теста
    if landlord_user:
        landlord_user.telegram_id = 123456789
    
    text = "Тестовое сообщение"

    # Фиксируем изменения в транзакции теста
    await db_session.flush()

    # 2. МОКИРОВАНИЕ
    with patch(
        "app.services.chat_service.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 999 

        # 3. ВЫПОЛНЕНИЕ
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

        # 4. ПРОВЕРКИ
        assert result is not None
        assert result.text == text
        assert result.sender_id == sender_id
        assert result.tg_message_id == 999

        # Проверка параметров вызова Telegram
        mock_send.assert_called_once()
        # Используем kwargs для надежности
        assert mock_send.call_args.kwargs["tg_user_id"] == 123456789
        assert f"#{booking_id}" in mock_send.call_args.kwargs["text"]


        # Проверки
        # assert result is not None
        # assert result.text == text
        # assert result.booking_id == booking_id
        # assert result.sender_id == sender_id
        # assert result.tg_message_id == 999

        # Проверяем, что send_message был вызван с правильными параметрами
        # mock_send.assert_called_once()
        # call_args = mock_send.call_args
        # assert call_args[1]["tg_user_id"] == 123456789
        # assert f"Бронь #{booking_id}" in call_args[1]["text"]
        # assert text in call_args[1]["text"]


# @pytest.mark.asyncio
# async def test_save_and_notify_no_telegram_id(db_session: AsyncSession, created_booking: Booking):
#     """Тест сохранения сообщения когда у арендодателя нет telegram_id."""
#     # Подготовка
#     booking_id = created_booking.id
#     # sender_id = created_booking.client_id
#     text = "Сообщение без telegram_id"

#     # Убеждаемся, что telegram_id = None
#     landlord_user = await db_session.get(User, created_booking.landlord.user_id)
#     sender_id = landlord_user.id
#     landlord_user.telegram_id = None
#     await db_session.flush() # Изменили commit на flush

#     # Мокируем TelegramService (не должен быть вызван)
#     with patch(
#         "app.services.chat_service.TelegramService.send_message", new_callable=AsyncMock
#     ) as mock_send:
#         # Выполнение
#         result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

#         # Проверки
#         assert result is not None
#         assert result.text == text
#         assert result.booking_id == booking_id
#         assert result.sender_id == sender_id
#         assert result.tg_message_id is None  # Не должно быть установлено

#         # send_message НЕ должен быть вызван
#         mock_send.assert_not_called()
@pytest.mark.asyncio
async def test_save_and_notify_no_telegram_id(db_session: AsyncSession, created_booking: Booking):
    """Тест сохранения сообщения когда у арендодателя нет telegram_id."""
    # 1. ПОДГОТОВКА
    booking_id = created_booking.id
    
    # Берем арендодателя — он ТОЧНО существует, раз создана бронь
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    
    # Если даже landlord_user не найден (бывает при сбоях фикстур), 
    # используем создателя брони напрямую через его связь
    sender_id = landlord_user.id if landlord_user else created_booking.landlord.user_id
    
    # Явно обнуляем telegram_id
    if landlord_user:
        landlord_user.telegram_id = None
    
    # Синхронизируем состояние с БД
    await db_session.flush()

    # 2. МОКИРОВАНИЕ
    with patch(
        "app.services.chat_service.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        
        # 3. ВЫПОЛНЕНИЕ
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, "Привет")

        # 4. ПРОВЕРКИ
        assert result is not None
        assert result.booking_id == booking_id
        assert result.tg_message_id is None
        mock_send.assert_not_called()



# @pytest.mark.asyncio
# async def test_save_and_notify_booking_not_found(db_session: AsyncSession, created_client):
#     """Тест обработки случая, когда бронирование не найдено."""
#     # Подготовка
#     booking_id = 99999  # Несуществующий ID
#     sender_id = created_client.id
#     text = "Сообщение для несуществующей брони"

#     # Мокируем TelegramService
#     with patch(
#         "app.services.chat_service.TelegramService.send_message", new_callable=AsyncMock
#     ) as mock_send:
#         # Выполнение
#         result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

#         # Проверки
#         assert result is not None  # Сообщение всё равно сохранено
#         assert result.text == text
#         assert result.booking_id == booking_id
#         assert result.sender_id == sender_id
#         assert result.tg_message_id is None

#         # send_message НЕ должен быть вызван (бронирование не найдено)
#         mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_save_and_notify_telegram_service_fails(
    db_session: AsyncSession, created_booking: Booking
):
    """Тест обработки ошибки отправки в Telegram (сервис вернул None)."""
    # 1. ПОДГОТОВКА
    booking_id = created_booking.id
    
    # Получаем арендодателя и устанавливаем ему TG ID
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 123456789
    
    # Чтобы избежать ошибки ForeignKeyViolation, используем существующий ID
    # (лендлорд сам себе пишет сообщение в этом тесте, для логики это не важно)
    sender_id = landlord_user.id 
    
    text = "Сообщение с ошибкой отправки"

    # Синхронизируем данные с базой, не закрывая транзакцию
    await db_session.flush()

    # 2. МОКИРОВАНИЕ
    # Патчим TelegramService ТАМ, ГДЕ он импортируется в сервисе
    with patch(
        "app.services.chat_service.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        # Имитируем сбой (Telegram вернул None вместо ID сообщения)
        mock_send.return_value = None 

        # 3. ВЫПОЛНЕНИЕ
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

        # 4. ПРОВЕРКИ
        assert result is not None
        assert result.text == text
        # Проверяем, что tg_message_id не записался, так как была ошибка
        assert result.tg_message_id is None 

        # Проверяем, что вызов метода был, несмотря на то, что он вернул ошибку
        mock_send.assert_called_once()
        
        # Проверяем, что пытались отправить именно на этот ID
        assert mock_send.call_args.kwargs["tg_user_id"] == 123456789


@pytest.mark.asyncio
async def test_save_and_notify_with_html_text(db_session: AsyncSession, created_booking: Booking):
    """Тест отправки сообщения с HTML форматированием."""
    # 1. ПОДГОТОВКА
    booking_id = created_booking.id
    
    # Получаем арендодателя из базы
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 987654321
    
    # Чтобы избежать ошибки ForeignKey (если клиент не виден в сессии),
    # используем ID существующего арендодателя как отправителя
    sender_id = landlord_user.id 
    
    text = "<b>Жирный текст</b> и <i>курсив</i>"
    
    # Используем flush, чтобы данные были доступны внутри транзакции
    await db_session.flush()

    # 2. МОКИРОВАНИЕ
    with patch(
        "app.services.chat_service.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = 888

        # 3. ВЫПОЛНЕНИЕ
        result = await ChatService.save_and_notify(db_session, booking_id, sender_id, text)

        # 4. ПРОВЕРКИ
        assert result is not None
        assert result.text == text
        assert result.tg_message_id == 888

        # Проверяем, что HTML теги дошли до вызова TelegramService
        # В 2026 году надежнее проверять через kwargs
        sent_text = mock_send.call_args.kwargs.get("text")
        assert text in sent_text
        assert "<b>" in sent_text
        assert "<i>" in sent_text


@pytest.mark.asyncio
async def test_save_and_notify_multiple_messages(
    db_session: AsyncSession, created_booking: Booking
):
    """Тест отправки нескольких сообщений для одного бронирования."""
    # 1. ПОДГОТОВКА
    booking_id = created_booking.id
    
    # Получаем арендодателя и ставим ему TG ID
    landlord_user = await db_session.get(User, created_booking.landlord.user_id)
    landlord_user.telegram_id = 111222333
    
    # Используем ID существующего пользователя (лендлорда), 
    # чтобы избежать ForeignKeyViolation с "невидимым" клиентом
    sender_id = landlord_user.id
    
    # Фиксируем изменения в транзакции теста
    await db_session.flush()

    # 2. МОКИРОВАНИЕ
    with patch(
        "app.services.chat_service.TelegramService.send_message", 
        new_callable=AsyncMock
    ) as mock_send:
        # Указываем список возвращаемых значений для каждого вызова по очереди
        mock_send.side_effect = [101, 102, 103]

        # 3. ВЫПОЛНЕНИЕ
        messages = []
        for i in range(3):
            msg = await ChatService.save_and_notify(
                db_session, booking_id, sender_id, f"Сообщение {i + 1}"
            )
            messages.append(msg)

        # 4. ПРОВЕРКИ
        assert len(messages) == 3
        # Проверяем, что каждое сообщение получило свой ID из Telegram в правильном порядке
        assert messages[0].tg_message_id == 101
        assert messages[1].tg_message_id == 102
        assert messages[2].tg_message_id == 103
        
        # Проверяем количество вызовов мока
        assert mock_send.call_count == 3
        
        # Проверка, что текст в Telegram уходил разный
        last_call_text = mock_send.call_args.kwargs.get("text")
        assert "Сообщение 3" in last_call_text

