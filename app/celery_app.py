import os
from celery import Celery
from celery.schedules import crontab

# Используем Redis как брокер (стандарт 2026 года)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "posutochka_tasks",
    broker=CELERY_BROKER_URL,
    include=["app.services.coins_tasks"]  # Путь к вашим задачам
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
)

# Настройка расписания Beat
celery_app.conf.beat_schedule = {
    "cleanup-expired-coins-every-night": {
        "task": "app.services.coins_tasks.cleanup_expired_coins_task",
        "schedule": crontab(hour=3, minute=0),  # Каждый день в 3 часа ночи
    },
}
