import pytest
from decimal import Decimal
from sqlalchemy import select, func
from app.models import Transaction, OwnerEarning, Payment, Balance, Landlord, Investor, Booking
from app.models.transaction import TransactionType
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, select
from datetime import datetime, timezone
from app.services.finance import FinanceService


# Эти константы должны быть доступны в тесте (либо импортированы, либо прописаны)
COMMISSION_RATE = Decimal("0.15") 
TAX_RATE = Decimal("0.06")
INVESTOR_POOL_RATE = Decimal("0.40") # 40% от чистой прибыли


'''Вот подробный разбор:

    test_finance_distribution_logic (первый вариант):
        Проверяет создание транзакций и запись в OwnerEarning.
        Проверяет только типы транзакций и ID получателей, но не проверяет суммы (деньги).
    test_finance_distribution_logic0 (второй вариант):
        Здесь вы добавили расчеты сумм через Decimal.
        Добавили проверку итоговых балансов в таблице Balance.
        Это расширенная версия первого теста.
    test_finance_distribution_logic1 (третий вариант):
        Это полная копия варианта logic0 (просто изменена цифра в названии функции на 1).'''
@pytest.mark.asyncio
async def test_finance_distribution_logic(
    db_session,
    created_booking,
    mock_owner_profile,
    mock_investor_profile,
    mock_landlord_profile
):
    """Тест проверяет распределение денег между лендлордом, владельцем и инвестором."""
    
    # 0. ПРИВЯЗКА ЛЕНДЛОРДА
    res = await db_session.execute(
        select(Landlord).where(Landlord.user_id == mock_landlord_profile.id)
    )
    landlord_record = res.scalar_one()
    created_booking.landlord_id = landlord_record.id
    
    # 1. Подготовка: добавляем платеж
    payment = Payment(
        amount=created_booking.cost, 
        payment_status="paid", 
        booking_id=created_booking.id
    )
    db_session.add(payment)
    
    # Используем flush вместо commit, чтобы объекты остались "живыми" в сессии
    await db_session.flush()
    # Обновляем объект, чтобы он точно знал свой статус и ID
    await db_session.refresh(created_booking) 

    # 2. Запускаем распределение
    service = FinanceService(db_session)
    await service.process_booking_completion(created_booking.id)
    
    # Синхронизируем созданные транзакции с базой перед проверкой
    await db_session.flush()

    # --- РАСЧЕТ ОЖИДАЕМЫХ СУММ ---
    # Используем Decimal для всех вычислений, чтобы избежать 0.000000001 ошибок
    total_price = created_booking.cost
    commission = total_price * COMMISSION_RATE
    landlord_amount = total_price - commission
    tax_amount = commission * TAX_RATE
    net_profit = commission - tax_amount

    investor_pool = net_profit * INVESTOR_POOL_RATE
    remaining_profit = net_profit - investor_pool

    # --- ПРОВЕРКИ ТРАНЗАКЦИЙ ---
    res = await db_session.execute(
        select(Transaction).where(Transaction.booking_id == created_booking.id)
    )
    transactions = res.scalars().all()
    
    # Проверяем, что создано нужное количество транзакций (например, 3)
    assert len(transactions) >= 3
    
    payout_details = {tx.transaction_type: (tx.user_id, tx.amount) for tx in transactions}

    # Проверка выплат
    assert payout_details[TransactionType.HOST_PAYOUT] == (mock_landlord_profile.id, landlord_amount)
    assert payout_details[TransactionType.OWNER_DIVIDEND] == (mock_owner_profile.id, remaining_profit)
    assert payout_details[TransactionType.INVESTOR_PAYOUT] == (mock_investor_profile.id, investor_pool)

    # --- ПРОВЕРКА БАЛАНСОВ ---
    res_balances = await db_session.execute(
        select(Balance).where(Balance.user_id.in_([
            mock_landlord_profile.id, 
            mock_owner_profile.id, 
            mock_investor_profile.id
        ]))
    )
    balances = res_balances.scalars().all()
    balance_map = {b.user_id: b.current_balance for b in balances}

    # Важно: если начальный баланс был не 0, прибавляйте суммы к нему!
    assert balance_map[mock_landlord_profile.id] == landlord_amount
    assert balance_map[mock_owner_profile.id] == remaining_profit
    assert balance_map[mock_investor_profile.id] == investor_pool


@pytest.mark.asyncio
async def test_finance_full_coverage_scenarios(db_session, created_booking):
    """
    Закрывает строки 128-134 (создание баланса) и 64 (отсутствие инвесторов).
    """
    # 1. Обеспечиваем выполнение условия is_fully_paid
    # Создаем платеж на полную стоимость (1000.0)
    full_payment = Payment(
        booking_id=created_booking.id,
        amount=created_booking.cost,
        payment_status="paid",
        payment_date=datetime.now(timezone.utc)
    )
    db_session.add(full_payment)
    
    # 2. Убираем инвесторов, чтобы покрыть строку 64 (if not investors: return)
    await db_session.execute(delete(Investor))
    
    # 3. Подгружаем лендлорда и удаляем его баланс для покрытия строк 128-134
    stmt = (
        select(Booking)
        .options(selectinload(Booking.landlord))
        .where(Booking.id == created_booking.id)
    )
    res = await db_session.execute(stmt)
    booking = res.scalar_one()
    
    # Удаляем существующий баланс
    await db_session.execute(
        delete(Balance).where(Balance.user_id == booking.landlord.user_id)
    )
    await db_session.commit()

    # 4. Запускаем сервис
    service = FinanceService(db_session)
    await service.process_booking_completion(booking.id)

    # 5. Проверка покрытия и результата
    # Проверяем, что баланс создался (строка 128)
    res_balance = await db_session.execute(
        select(Balance).where(Balance.user_id == booking.landlord.user_id)
    )
    new_balance = res_balance.scalar_one_or_none()
    
    assert new_balance is not None
    assert new_balance.current_balance > 0

@pytest.mark.asyncio
async def test_process_booking_unpaid_raises_error(db_session, created_booking):
    service = FinanceService(db_session)
    # Убеждаемся, что платежей нет (is_fully_paid будет False)
    with pytest.raises(ValueError, match="Бронирование не оплачено полностью"):
        await service.process_booking_completion(created_booking.id)