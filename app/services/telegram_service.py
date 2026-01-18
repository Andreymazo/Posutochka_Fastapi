'''Что этот сервис делает для вашего чата:

    Связь без сокетов: Когда клиент пишет в API (на сайте), ваш бэкенд вызывает этот метод и отправляет текст Арендодателю прямо в Telegram.
    Память сообщений: Мы возвращаем message_id. Вы запишете его в таблицу message (поле tg_message_id).
    2026 Ready: Мы используем асинхронный httpx, что идеально ложится в архитектуру FastAPI и не блокирует основной поток приложения.

Следующий шаг:
Теперь нам нужен Webhook-роутер. Это будет эндпоинт в вашем FastAPI, куда Telegram будет присылать ответы Арендодателя.
Готовы написать app/routers/chat.py и логику обработки ответов "Reply"?'''
import os
import httpx
import logging

logger = logging.getLogger(__name__)

# Читаем токен так же, как вы читаете DATABASE_URL
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class TelegramService:
    @staticmethod
    async def send_message(tg_user_id: int, text: str) -> int | None:
        """
        Отправляет сообщение пользователю в Telegram.
        Возвращает tg_message_id, чтобы мы могли опознать Reply (ответ) позже.
        """
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN не установлен в окружении!")
            return None

        url = f"https://api.telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": tg_user_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                # Возвращаем ID сообщения в Telegram
                return result["result"]["message_id"]
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
                return None
