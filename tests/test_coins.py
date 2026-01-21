import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from app.models import CoinsTransaction, User
from app.services.coins_tasks import cleanup_expired_coins
from unittest.mock import patch, AsyncMock,  MagicMock


@pytest.mark.asyncio
async def test_coins_expiration_logic(db_session, created_landlord_user: User):
    """Тест логики сгорания бонусов на уровне SQL-запроса."""
    # 1. ПОДГОТОВКА
    # Используем созданного юзера из твоей фикстуры
    user = created_landlord_user
    user.coins_balance = Decimal("100.00")
    
    # Создаем транзакцию, которая истекла вчера
    expired_bonus = CoinsTransaction(
        user_id=user.id,
        amount=Decimal("100.00"),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        is_active=True,
        source_app="posutochka"
    )
    db_session.add(expired_bonus)
    
    # Синхронизируем с базой, чтобы SQL-запрос в задаче увидел данные
    await db_session.flush()

    # 2. ВЫПОЛНЕНИЕ: Патчим AsyncSessionLocal, чтобы задача работала в нашей сессии
    with patch("app.services.coins_tasks.AsyncSessionLocal") as mock_session_local:
        # Заставляем "async with AsyncSessionLocal()" вернуть db_session из теста
        mock_session_local.return_value.__aenter__.return_value = db_session
        
        # Запускаем нашу SQL-логику
        await cleanup_expired_coins()

    # 3. ПРОВЕРКА
    # Обновляем объекты из базы, чтобы увидеть изменения после SQL-запроса
    await db_session.refresh(user)
    await db_session.refresh(expired_bonus)

    assert user.coins_balance == Decimal("0.00"), f"Баланс должен был обнулиться, но он {user.coins_balance}"
    assert expired_bonus.is_active is False, "Транзакция должна быть помечена как неактивная (is_active=False)"

@pytest.mark.asyncio
async def test_coins_partial_expiration(db_session, created_landlord_user: User):
    user = created_landlord_user
    user.coins_balance = Decimal("300.00")
    
    # Сгоревшая транзакция
    expired = CoinsTransaction(
        user_id=user.id, amount=Decimal("100.00"),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        is_active=True
    )
    # Свежая транзакция (не должна сгореть)
    fresh = CoinsTransaction(
        user_id=user.id, amount=Decimal("200.00"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=10),
        is_active=True
    )
    db_session.add_all([expired, fresh])
    await db_session.flush()

    with patch("app.services.coins_tasks.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = db_session
        await cleanup_expired_coins()

    await db_session.refresh(user)
    await db_session.refresh(expired)
    await db_session.refresh(fresh)

    # Должно остаться 200
    assert user.coins_balance == Decimal("200.00")
    assert expired.is_active is False
    assert fresh.is_active is True
@pytest.mark.asyncio
async def test_multiple_users_expiration(db_session, created_landlord_user: User, created_client_user: User):
    # Юзер 1: сгорает 50
    created_landlord_user.coins_balance = Decimal("100.00")
    tx1 = CoinsTransaction(user_id=created_landlord_user.id, amount=Decimal("50.00"), 
                           expires_at=datetime.now(timezone.utc) - timedelta(days=1), is_active=True)
    
    # Юзер 2: сгорает 30
    created_client_user.coins_balance = Decimal("100.00")
    tx2 = CoinsTransaction(user_id=created_client_user.id, amount=Decimal("30.00"), 
                           expires_at=datetime.now(timezone.utc) - timedelta(days=1), is_active=True)
    
    db_session.add_all([tx1, tx2])
    await db_session.flush()

    with patch("app.services.coins_tasks.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = db_session
        await cleanup_expired_coins()

    await db_session.refresh(created_landlord_user)
    await db_session.refresh(created_client_user)

    assert created_landlord_user.coins_balance == Decimal("50.00")
    assert created_client_user.coins_balance == Decimal("70.00")
    

@pytest.mark.asyncio
async def test_activate_client_bonus_logic(db_session, created_client_user: User):
    # 1. ПОДГОТОВКА
    user = created_client_user
    user.coins_balance = Decimal("0.00")
    
    new_bonus = CoinsTransaction(
        user_id=user.id,
        amount=Decimal("150.00"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_active=True,
        source_app="posutochka"
    )
    db_session.add(new_bonus)
    await db_session.flush() # Данные теперь видны внутри этой сессии

    # 2. ВЫПОЛНЕНИЕ: Передаем сессию из теста внутрь функции
    from app.services.coins_tasks import activate_client_bonus
    await activate_client_bonus(new_bonus.id, db=db_session)

    # 3. ПРОВЕРКА
    await db_session.refresh(user)
    assert user.coins_balance == Decimal("150.00")

@pytest.mark.asyncio
async def test_landlord_booking_reward_full_link(db_session, created_landlord_user: User, created_booking):
    user = created_landlord_user
    user.coins_balance = Decimal("500.00")
    # Предположим, у вас есть ID бронирования (можно создать фиктивное или реальное)
    
    
    from app.services.coins_service import process_landlord_booking_reward
    
    await process_landlord_booking_reward(
        landlord_id=user.id, 
        total_price=1000.0, 
        booking_id=created_booking.id, 
        db=db_session
    )

    await db_session.refresh(user)
    
    # Проверяем связь в базе
    from sqlalchemy import select
    stmt = select(CoinsTransaction).where(CoinsTransaction.booking_id == created_booking.id)
    result = await db_session.execute(stmt)
    tx = result.scalar_one()
    
    assert tx.user_id == user.id
    assert tx.amount == Decimal("100.00")
    assert tx.booking_id == created_booking.id


@pytest.mark.asyncio
async def test_activate_client_bonus_standalone_coverage():
    """Закрываем ветку 'if db is None' в coins_tasks.py для 100% покрытия."""
    
    # Мокаем транзакцию
    mock_tx = AsyncMock()
    mock_tx.id = 1
    mock_tx.user_id = 999
    mock_tx.amount = 100.0
    mock_tx.is_active = True

    # Мокаем сессию БД
    mock_session = AsyncMock()
    # Заставляем db.get возвращать нашу мок-транзакцию
    mock_session.get.return_value = mock_tx
    
    # Мокаем контекстный менеджер AsyncSessionLocal
    with patch("app.services.coins_tasks.AsyncSessionLocal") as mock_session_factory:
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        
        from app.services.coins_tasks import activate_client_bonus
        
        # Вызываем БЕЗ db (зайдет в if db is None)
        await activate_client_bonus(transaction_id=1)
        
        # ПРОВЕРКИ для покрытия:
        mock_session_factory.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_landlord_reward_standalone_coverage():
    """Закрываем ветку 'if db is None' в coins_service.py для 100% покрытия."""
    
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    with patch("app.services.coins_service.AsyncSessionLocal") as mock_session_factory:
        mock_session_factory.return_value.__aenter__.return_value = mock_session
        
        from app.services.coins_service import process_landlord_booking_reward
        
        # Вызываем БЕЗ db
        await process_landlord_booking_reward(landlord_id=1, total_price=1000.0, booking_id=1)
        
        mock_session_factory.assert_called_once()
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_client_booking_bonus_logic(db_session, created_client_user, created_booking):
    """
    Тест системы премирования клиента:
    1. Расчет 3% от суммы.
    2. Создание транзакции в БД.
    3. Вызов Celery задачи с задержкой (countdown).
    """
    from app.services.coins_service import process_client_booking_bonus
    
    # Исходные данные
    total_price = 10000.0  # 3% должно быть 300.00
    
    # Патчим apply_async у Celery задачи, чтобы проверить вызов
    with patch("app.services.coins_tasks.activate_client_bonus_task.apply_async") as mock_celery:
        
        # Выполняем начисление
        bonus_amount = await process_client_booking_bonus(
            client_id=created_client_user.id,
            total_price=total_price,
            booking_id=created_booking.id,
            db=db_session
        )

        # 1. Проверяем математику
        assert bonus_amount == Decimal("300.00")

        # 2. Проверяем запись в БД
        from sqlalchemy import select
        from app.models import CoinsTransaction
        
        stmt = select(CoinsTransaction).where(
            CoinsTransaction.booking_id == created_booking.id,
            CoinsTransaction.user_id == created_client_user.id
        )
        result = await db_session.execute(stmt)
        tx = result.scalar_one()
        
        assert tx.amount == Decimal("300.00")
        assert "3%" in tx.description

        # 3. Проверяем, что Celery получил команду на запуск через 30 дней
        mock_celery.assert_called_once()
        # Получаем аргументы вызова
        called_args, called_kwargs = mock_celery.call_args

        # В Celery apply_async(args=[...], countdown=...) параметры попадают в kwargs
        assert called_kwargs["args"] == [tx.id]  # Проверяем список ID транзакции
        assert called_kwargs["countdown"] == 30 * 24 * 60 * 60  # Проверяем задерж
       