import pytest
from decimal import Decimal
from sqlalchemy import select
from app.models import Transaction, OwnerEarning, Payment
from app.models.transaction import TransactionType
from app.services.finance import FinanceService

@pytest.mark.asyncio
async def test_finance_distribution_logic(
    db_session,
    created_booking,
    mock_owner_profile,
    mock_investor_profile,
    mock_landlord_profile
):
    """Тест проверяет распределение денег между лендлордом, владельцем и инвестором."""
    
    # 1. Подготовка: делаем бронь оплаченной (чтобы сервис не выкинул ValueError)
    # Используем стоимость из созданной фикстуры booking
    payment = Payment(
        amount=created_booking.cost,
        payment_status="paid",
        booking_id=created_booking.id
    )
    db_session.add(payment)
    await db_session.commit()

    # 2. Инициализируем сервис и запускаем распределение
    service = FinanceService(db_session)
    await service.process_booking_completion(created_booking.id)
    await db_session.commit()

    # 3. ПРОВЕРКА: Транзакции в истории
    res = await db_session.execute(
        select(Transaction).where(Transaction.booking_id == created_booking.id)
    )
    transactions = res.scalars().all()
    
    tx_types = [tx.transaction_type for tx in transactions]
    
    # Проверяем, что создано минимум 3 транзакции (Host, Owner, Investor)
    assert len(transactions) >= 3
    assert TransactionType.HOST_PAYOUT in tx_types
    assert TransactionType.OWNER_DIVIDEND in tx_types
    assert TransactionType.INVESTOR_PAYOUT in tx_types

    # 4. ПРОВЕРКА: Создание записи в OwnerEarning (спец. таблица для владельца)
    res_oe = await db_session.execute(
        select(OwnerEarning).where(OwnerEarning.booking_id == created_booking.id)
    )
    earning = res_oe.scalar_one_or_none()
    assert earning is not None
    assert earning.amount > 0
    assert earning.user_id == mock_owner_profile.id
