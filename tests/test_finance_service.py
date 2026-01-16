import pytest
from decimal import Decimal
from sqlalchemy import select, func
from app.models import Transaction, OwnerEarning, Payment, Balance, Landlord
from app.models.transaction import TransactionType
from app.services.finance import FinanceService
from sqlalchemy.orm import selectinload

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
    
    # 0. ПРИВЯЗКА ЛЕНДЛОРДА (решение предыдущих ошибок)
    # Находим запись Landlord, связанную с mock_landlord_profile (User ID)
    res = await db_session.execute(
        select(Landlord).where(Landlord.user_id == mock_landlord_profile.id)
    )
    landlord_record = res.scalar_one()
    created_booking.landlord_id = landlord_record.id
    
    # 1. Подготовка: делаем бронь оплаченной и коммитим изменения
    payment = Payment(amount=created_booking.cost, payment_status="paid", booking_id=created_booking.id)
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(created_booking) # Обновляем объект брони в памяти

    # 2. Инициализируем сервис и запускаем распределение
    service = FinanceService(db_session)
    await service.process_booking_completion(created_booking.id)
    await db_session.commit()

    # --- РАСЧЕТ ОЖИДАЕМЫХ СУММ ---
    total_price = created_booking.cost # Например, 1000.00
    commission = total_price * Decimal("0.15")
    landlord_amount = total_price - commission # 850.00
    tax_amount = commission * Decimal("0.06") # 9.00
    net_profit = commission - tax_amount # 141.00

    investor_pool = net_profit * Decimal("0.40") # 56.40
    remaining_profit = net_profit - investor_pool # 84.60 (это доля владельца)

    # --- ПРОВЕРКИ ТРАНЗАКЦИЙ И СУММ ---
    res = await db_session.execute(
        select(Transaction).where(Transaction.booking_id == created_booking.id)
    )
    transactions = res.scalars().all()
    
    # Словарь для проверки сумм и user_id: {тип_транзакции: (user_id, amount)}
    payout_details = {
        tx.transaction_type: (tx.user_id, tx.amount) 
        for tx in transactions
    }

    # Проверка выплаты лендлорду (HOST_PAYOUT)
    assert payout_details[TransactionType.HOST_PAYOUT][0] == mock_landlord_profile.id
    assert payout_details[TransactionType.HOST_PAYOUT][1] == landlord_amount 

    # Проверка дивидендов владельцу (OWNER_DIVIDEND)
    assert payout_details[TransactionType.OWNER_DIVIDEND][0] == mock_owner_profile.id
    assert payout_details[TransactionType.OWNER_DIVIDEND][1] == remaining_profit 

    # Проверка инвестору (INVESTOR_PAYOUT)
    assert payout_details[TransactionType.INVESTOR_PAYOUT][0] == mock_investor_profile.id
    assert payout_details[TransactionType.INVESTOR_PAYOUT][1] == investor_pool
    
    # ... (Остальные проверки количества и типов транзакций, OwnerEarning) ...

    # --- ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА БАЛАНСОВ ПОЛЬЗОВАТЕЛЕЙ ---
    # Проверим, что итоговые балансы в таблице 'balance' обновились корректно
    res_balances = await db_session.execute(
        select(Balance).where(Balance.user_id.in_([
            mock_landlord_profile.id, 
            mock_owner_profile.id, 
            mock_investor_profile.id
        ]))
    )
    balances = res_balances.scalars().all()
    balance_map = {b.user_id: b.current_balance for b in balances}

    assert balance_map[mock_landlord_profile.id] == landlord_amount
    assert balance_map[mock_owner_profile.id] == remaining_profit
    assert balance_map[mock_investor_profile.id] == investor_pool
