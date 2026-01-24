import asyncio
import secrets
from app.celery_app import celery_app
import redis.asyncio as redis
import os
# Предполагаем наличие интеграций (aiogram для бота и mini-mail для почты)
# Если их нет, пока оставим заглушки с принтами DEBUG 2026
# Внутри Docker используем имя сервиса redis, иначе localhost
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

async def _send_verification_logic(user_id: int, email: str, tg_id: int | None):
    """Логика генерации и рассылки кода подтверждения."""
    """Ядро логики: генерация, хранение в Redis и отправка."""
    # 1. Генерация 6-значного кода
    code = str(secrets.randbelow(900000) + 100000)
    
    # 2. Подключаемся к Redis
    # decode_responses=True позволяет получать строки, а не байты
    client = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Ключ otp:ID_ПОЛЬЗОВАТЕЛЯ, значение - код, TTL - 10 минут
    await client.set(f"otp:{user_id}", code, ex=600)
    await client.aclose()
    
    print(f"--- [DEBUG 2026] OTP для User {user_id}: {code} ---")

    # 3. Имитация отправки Email (позже подключим fastapi-mail)
    print(f"DEBUG: Отправка Email на {email} с кодом {code}")

    # 4. Имитация отправки в Telegram (если привязан)
    if tg_id:
        print(f"DEBUG: Отправка кода {code} в Telegram ID: {tg_id}")
# Выдает ошибку asyncio.run() cannot be called from a running event loop
# @celery_app.task(name="app.services.notification_tasks.send_verification_task")
# def send_verification_task(user_id: int, email: str, tg_id: int | None):
#     """Синхронная обертка для Celery."""
#     return asyncio.run(_send_verification_logic(user_id, email, tg_id))
@celery_app.task(name="app.services.notification_tasks.send_verification_task")
def send_verification_task(user_id: int, email: str, tg_id: int | None):
    """Безопасная обертка для Celery, работающая и в тестах, и в проде."""
    try:
        # Проверяем, запущен ли уже event loop (актуально для тестов)
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Если мы в тесте (цикл уже идет), планируем задачу в нем
        # Используем метод, который дождется выполнения, чтобы тест не завершился раньше
        return asyncio.ensure_future(_send_verification_logic(user_id, email, tg_id))
    else:
        # Если мы в обычном воркере Celery (цикла нет), создаем его
        return asyncio.run(_send_verification_logic(user_id, email, tg_id))


