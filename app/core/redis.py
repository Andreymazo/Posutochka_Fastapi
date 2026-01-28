import redis.asyncio as redis

# Параметры из твоего docker-compose. localhost для локльной и редис для контейнеров
REDIS_URL = "redis://redis:6379/0" 

async def get_redis():
    return redis.from_url(REDIS_URL, decode_responses=True)