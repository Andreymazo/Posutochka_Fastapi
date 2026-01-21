from datetime import datetime, timezone
import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models import CoinsTransaction, User
from app.celery_app import celery_app
from sqlalchemy.ext.asyncio import AsyncSession


async def cleanup_expired_coins():
    """Массовое списание просроченных бонусов (асинхронно)."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        
        # 1. Находим все транзакции, которые истекли
        stmt = (
            select(CoinsTransaction)
            .where(CoinsTransaction.expires_at <= now)
            .where(CoinsTransaction.is_active == True)
        )
        result = await db.execute(stmt)
        expired_txs = result.scalars().all()
        
        for tx in expired_txs:
            # 2. Вычитаем из баланса пользователя (используем tx.user_id!)
            await db.execute(
                update(User)
                .where(User.id == tx.user_id)
                .values(coins_balance=User.coins_balance - tx.amount)
            )
            # 3. Деактивируем транзакцию
            tx.is_active = False
            
        await db.commit()
        if expired_txs:
            print(f"DEBUG [2026]: Списаны бонусы по {len(expired_txs)} транзакциям.")


async def activate_client_bonus(transaction_id: int, db: AsyncSession = None):
    """
    Если db передана (тест), используем её. 
    Если нет (Celery), создаем новую.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            result = await _activate_logic(transaction_id, session)
            # ВАЖНО для 2026 года: фиксируем изменения в автономном режиме
            await session.commit() 
            return result
    else:
        # В тестах commit сделает фикстура или сам тест
        return await _activate_logic(transaction_id, db)


async def _activate_logic(transaction_id: int, db: AsyncSession):
    tx = await db.get(CoinsTransaction, transaction_id)
    if not tx or not tx.is_active:
        return

    await db.execute(
        update(User)
        .where(User.id == tx.user_id)
        .values(coins_balance=User.coins_balance + tx.amount)
    )
    # ВАЖНО: Мы делаем flush, чтобы изменения применились в рамках текущей транзакции теста
    await db.flush() 

@celery_app.task(name="app.services.coins_tasks.activate_client_bonus_task")
def activate_client_bonus_task(transaction_id: int):
    """Синхронная обертка, устойчивая к запущенному event loop (тестам)."""
    try:
        # Проверяем, есть ли уже запущенный цикл (как в тестах)
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Если мы в тесте, используем create_task или просто await
        # В режиме eager Celery это сработает корректно
        return loop.create_task(activate_client_bonus(transaction_id))
    else:
        # Если мы в реальном Celery-воркере (цикла нет), запускаем новый
        return asyncio.run(activate_client_bonus(transaction_id))


@celery_app.task(name="app.services.coins_tasks.cleanup_expired_coins_task")
def cleanup_expired_coins_task():
    """Умная обертка для ежедневной очистки."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return loop.create_task(cleanup_expired_coins())
    else:
        return asyncio.run(cleanup_expired_coins())

# @celery_app.task(name="app.services.coins_tasks.activate_client_bonus_task")
# def activate_client_bonus_task(transaction_id: int):
#     """Обертка для активации бонуса клиента через 30 дней."""
#     return asyncio.run(activate_client_bonus(transaction_id))

# async def activate_client_bonus(transaction_id: int):
#     """Логика активации бонуса."""
#     async with AsyncSessionLocal() as db:
#         tx = await db.get(CoinsTransaction, transaction_id)
#         if not tx or not tx.is_active:
#             return

#         # ИСПРАВЛЕНО: User.id == tx.user_id
#         await db.execute(
#             update(User)
#             .where(User.id == tx.user_id) 
#             .values(coins_balance=User.coins_balance + tx.amount)
#         )
#         await db.commit()


# from datetime import datetime, timezone
# from sqlalchemy import select, update
# from app.database import AsyncSessionLocal
# from app.models import CoinsTransaction, User

# import asyncio
# from app.celery_app import celery_app
# from app.services.coins_service import cleanup_expired_coins # Ваш SQL метод


# async def cleanup_expired_coins():
#     """
#     Задача по расписанию (раз в сутки).
#     Находит все активные транзакции, срок которых истек, 
#     и вычитает их сумму из баланса пользователя.
#     """
#     async with AsyncSessionLocal() as db:
#         now = datetime.now(timezone.utc)
        
#         # 1. Находим все транзакции, которые истекли, но еще активны
#         stmt = (
#             select(CoinsTransaction)
#             .where(CoinsTransaction.expires_at <= now)
#             .where(CoinsTransaction.is_active == True)
#         )
#         result = await db.execute(stmt)
#         expired_txs = result.scalars().all()
        
#         for tx in expired_txs:
#             # 2. Вычитаем из баланса пользователя
#             await db.execute(
#                 update(User)
#                 .where(User.id == tx.user_id)
#                 .values(coins_balance=User.coins_balance - tx.amount)
#             )
#             # 3. Помечаем транзакцию как неактивную (сгоревшую)
#             tx.is_active = False
            
#         await db.commit()
#         if expired_txs:
#             print(f"DEBUG: Списаны бонусы по {len(expired_txs)} истекшим транзакциям.")

# @celery_app.task(name="app.services.coins_tasks.cleanup_expired_coins_task")
# def cleanup_expired_coins_task():
#     """Обертка для запуска асинхронной задачи в Celery"""
#     loop = asyncio.get_event_loop()
#     if loop.is_running():
#         # Если вдруг цикл уже запущен
#         future = asyncio.ensure_future(cleanup_expired_coins())
#         return future
#     else:
#         return asyncio.run(cleanup_expired_coins())



# async def activate_client_bonus(transaction_id: int):
#     """
#     Задача, которая вызывается через 30 дней после бронирования.
#     Делает бонус доступным и прибавляет его к балансу клиента.
#     """
#     async with AsyncSessionLocal() as db:
#         tx = await db.get(CoinsTransaction, transaction_id)
#         if not tx or not tx.is_active:
#             return

#         # Прибавляем к балансу
#         await db.execute(
#             update(User)
#             .where(User.id == tx.id)
#             .values(coins_balance=User.coins_balance + tx.amount)
#         )
        
#         # Можно отправить уведомление в Telegram здесь же
#         await db.commit()
