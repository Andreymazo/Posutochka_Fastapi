import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.telegram_service import TelegramService

@pytest.mark.asyncio
async def test_send_message_no_token():
    """Тест случая, когда токен не установлен (покрывает logger.error)."""
    with patch("app.services.telegram_service.TELEGRAM_BOT_TOKEN", None):
        result = await TelegramService.send_message(123, "test")
        assert result is None

@pytest.mark.asyncio
async def test_send_message_http_status_error():
    """Тест ошибки статуса (например, 400 Bad Request от Telegram)."""
    # Мокируем контекстный менеджер AsyncClient
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=mock_response
    )
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client

    with patch("httpx.AsyncClient", return_value=mock_client):
        # Должен сработать блок except Exception
        result = await TelegramService.send_message(123, "test")
        assert result is None

@pytest.mark.asyncio
async def test_send_message_exception():
    """Тест любого другого исключения (например, ошибка соединения)."""
    mock_client = AsyncMock()
    mock_client.post.side_effect = Exception("Connection lost")
    mock_client.__aenter__.return_value = mock_client

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await TelegramService.send_message(123, "test")
        assert result is None

@pytest.mark.asyncio
async def test_send_message_success_complete():
    """Тест успешной отправки для закрепления покрытия основной ветки."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": {"message_id": 555}}
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client

    with patch("app.services.telegram_service.TELEGRAM_BOT_TOKEN", "fake_token"):
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await TelegramService.send_message(123, "test")
            assert result == 555
