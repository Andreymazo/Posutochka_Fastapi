from sqlalchemy import text
from app.database import AsyncSessionLocal
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import CoinsTransaction, User
from app.services.coins_tasks import activate_client_bonus_task

async def cleanup_expired_coins():
    """
    Массовое списание просроченных бонусов на уровне БД.
    Запускается фоновым процессом раз в сутки.
    """
    async with AsyncSessionLocal() as db:
        # SQL-запрос для 2026 года: эффективный UPDATE с подзапросом
        sql = """
        WITH expired_sums AS (
            SELECT user_id, SUM(amount) as total_expired
            FROM coins_transaction
            WHERE expires_at <= NOW() AND is_active = true
            GROUP BY user_id
        )
        UPDATE "user"
        SET coins_balance = "user".coins_balance - expired_sums.total_expired
        FROM expired_sums
        WHERE "user".id = expired_sums.user_id;

        UPDATE coins_transaction
        SET is_active = false
        WHERE expires_at <= NOW() AND is_active = true;
        """
        await db.execute(text(sql))
        await db.commit()


async def process_landlord_booking_reward(
    landlord_id: int, 
    total_price: float, 
    booking_id: int, 
    db: AsyncSession = None
):
    """
    Логика: Арендодатель платит 10% и получает 10% бонусами.
    Операция жестко привязана к booking_id.
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            result = await _landlord_reward_logic(landlord_id, total_price, booking_id, session)
            await session.commit()
            return result
    else:
        return await _landlord_reward_logic(landlord_id, total_price, booking_id, db)

async def _landlord_reward_logic(landlord_id: int, total_price: float, booking_id: int, db: AsyncSession):
    # 10% от суммы
    amount = Decimal(str(total_price)) * Decimal("0.10")
    # Бонусы живут 1 год
    expires_at = datetime.now(timezone.utc) + timedelta(days=365)

    # 1. Обновляем баланс пользователя (списание 10% и начисление 10%)
    # Математически баланс не меняется, но блокировка строки (Row Lock) важна для целостности
    await db.execute(
        update(User)
        .where(User.id == landlord_id)
        .values(coins_balance=User.coins_balance - amount + amount)
    )

    # 2. Создаем транзакцию с привязкой к брони
    new_tx = CoinsTransaction(
        user_id=landlord_id,
        booking_id=booking_id,
        amount=amount,
        expires_at=expires_at,
        is_active=True,
        source_app="posutochka",
        description=f"Кэшбэк 10% за бронирование #{booking_id}"
    )
    db.add(new_tx)
    
    # Делаем flush, чтобы внутри текущей транзакции ID транзакции монет стал доступен
    await db.flush()
    return amount

async def process_client_booking_bonus(client_id: int, total_price: float, booking_id: int, db: AsyncSession):
    """
    Клиент получает 3% бонусов через 30 дней после бронирования.
    """
    amount = Decimal(str(total_price)) * Decimal("0.03")
    # Бонусы сгорят через 1 год после того, как будут начислены
    expires_at = datetime.now(timezone.utc) + timedelta(days=30 + 365)

    # 1. Создаем транзакцию (is_active=True, но она еще не в балансе)
    new_tx = CoinsTransaction(
        user_id=client_id,
        booking_id=booking_id,
        amount=amount,
        expires_at=expires_at,
        is_active=True,
        source_app="posutochka",
        description=f"Бонус 3% за бронирование #{booking_id} (активация через 30 дней)"
    )
    db.add(new_tx)
    await db.flush() # Получаем ID транзакции

    # 2. Планируем задачу Celery на активацию через 30 дней (в секундах)
    # В 2026 году используем countdown для отложенного старта
    activate_client_bonus_task.apply_async(
        args=[new_tx.id], 
        countdown=30 * 24 * 60 * 60  # 30 дней
    )
    
    return amount

async def process_client_booking_bonus(client_id: int, total_price: float, booking_id: int, db: AsyncSession):
    """
    Начисление клиенту 3% бонусов. 
    Транзакция создается сейчас, баланс обновится через 30 дней через Celery.
    """
    amount = Decimal(str(total_price)) * Decimal("0.03")
    # Срок сгорания: 30 дней до активации + 365 дней жизни = 395 дней от текущей даты
    expires_at = datetime.now(timezone.utc) + timedelta(days=395)

    new_tx = CoinsTransaction(
        user_id=client_id,
        booking_id=booking_id,
        amount=amount,
        expires_at=expires_at,
        is_active=True,
        source_app="posutochka",
        description=f"Премия 3% за бронирование #{booking_id}"
    )
    db.add(new_tx)
    await db.flush() # Чтобы получить id транзакции для Celery

    # Ставим задачу в Celery на выполнение через 30 дней
    activate_client_bonus_task.apply_async(
        args=[new_tx.id], 
        countdown=30 * 24 * 60 * 60 # 2 592 000 секунд
    )
    return amount