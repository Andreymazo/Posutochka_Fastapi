import redis.asyncio as redis

REDIS_URL = "redis://localhost:6380/0" 

# Создаем пул соединений один раз при импорте модуля
redis_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

async def get_redis() -> redis.Redis:
    """Возвращает клиент Redis, использующий глобальный пул."""
    return redis.Redis(connection_pool=redis_pool)