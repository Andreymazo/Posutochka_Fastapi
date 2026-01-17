import pytest
from httpx import AsyncClient
from starlette import status
from app.models.transaction import TransactionType
from app.models import Balance
from sqlalchemy import select
from decimal import Decimal

@pytest.mark.asyncio
async def test_transactions_full_lifecycle(
    client: AsyncClient, 
    db_session, 
    created_booking,
    mock_landlord_profile
):
    # 0. Находим или создаем баланс для лендлорда, чтобы ForeignKey не ругался
    result = await db_session.execute(
        select(Balance).where(Balance.user_id == mock_landlord_profile.id)
    )
    balance = result.scalar_one_or_none()
    
    # Если фикстура mock_landlord_profile не создает баланс автоматически, создадим его
    if not balance:
        balance = Balance(user_id=mock_landlord_profile.id, current_balance=0)
        db_session.add(balance)
        await db_session.commit()
        await db_session.refresh(balance)

    balance_id = balance.id

    # 1. POST - Создание транзакции
    tx_data = {
        "user_id": mock_landlord_profile.id,
        "booking_id": created_booking.id,
        "balance_id": balance_id,  # Теперь ID реальный
        "amount": 850.00,
        "transaction_type": "host_payout" 
    }
    resp = await client.post("/transactions/", json=tx_data)
    assert resp.status_code == status.HTTP_201_CREATED
    tx_id = resp.json()["id"]

    # 2. GET List - Проверка фильтров (строки 21-24)
    # Проверяем фильтр по user_id
    resp = await client.get("/transactions/", params={"user_id": mock_landlord_profile.id})
    assert resp.status_code == 200
    assert any(t["id"] == tx_id for t in resp.json())

    # Проверяем фильтр по booking_id
    resp = await client.get("/transactions/", params={"booking_id": created_booking.id})
    assert resp.status_code == 200
    assert resp.json()[0]["booking_id"] == created_booking.id

    # 3. GET One (строки 36-39)
    resp = await client.get(f"/transactions/{tx_id}")
    assert resp.status_code == 200
    assert Decimal(str(resp.json()["amount"])) == Decimal("850.00")

    # 4. PATCH - Обновление типа (строки 67-76)
    # Проверяем строку 73: update_data["transaction_type"].value
    patch_data = {"transaction_type": "owner_dividend"}
    resp = await client.patch(f"/transactions/{tx_id}", json=patch_data)
    assert resp.status_code == 200
    assert resp.json()["transaction_type"] == "owner_dividend"
    # Покрывает ветку 72->75
    await client.patch(f"/transactions/{tx_id}", json={"amount": 10.0})


    # 5. DELETE (строки 88-92)
    resp = await client.delete(f"/transactions/{tx_id}")
    assert resp.status_code == 204

    # 6. 404 Error Coverage (строки 39, 69, 92)
    for method in ["get", "patch", "delete"]:
        call = getattr(client, method)
        kwargs = {"json": {"amount": 100}} if method == "patch" else {}
        resp = await call("/transactions/999999", **kwargs)
        assert resp.status_code == 404
