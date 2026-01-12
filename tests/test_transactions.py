"""Tests for Transaction API endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Balance, Booking, Transaction, User


@pytest.mark.asyncio
class TestTransactionEndpoints:
    """Tests for transaction CRUD operations."""

    async def test_create_transaction(
        self,
        client: AsyncClient,
        created_landlord_user: User,  # Используем существующую фикстуру
        created_booking: Booking,
        # Убедитесь, что у вас есть фикстура created_balance в conftest.py
        created_balance: Balance,
        sample_payment_data: dict[str, Any], # Используем имеющуюся фикстуру данных
    ) -> None:
        """Test creating a new transaction."""
        # Подготавливаем данные для создания транзакции
        transaction_data = {
            "amount": sample_payment_data["amount"],
            "transaction_type": "booking_payment", # или другое значение из Enum
            "user_id": created_landlord_user.id,
            "booking_id": created_booking.id,
            "balance_id": created_balance.id,
        }

        # ОБЯЗАТЕЛЬНО await для post
        response = await client.post("/transactions/", json=transaction_data)

        print(response.json()) # Это покажет, какое именно поле не нравится Pydantic
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == transaction_data["amount"]
        assert data["user_id"] == created_landlord_user.id
        assert data["booking_id"] == created_booking.id
        assert data["balance_id"] == created_balance.id

    async def test_get_transactions(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_landlord_user: User,  # Исправлено имя фикстуры
        created_booking: Booking,
        created_balance: Balance,
        sample_payment_data: dict[str, Any],
    ) -> None:
        """Test retrieving all transactions."""
        # 1. Создаем транзакцию напрямую в БД для теста получения
        transaction = Transaction(
            amount=sample_payment_data["amount"],
            # ИСПОЛЬЗУЕМ валидный тип из вашего Enum (например, 'booking_income')
            transaction_type="host_payout",
            user_id=created_landlord_user.id,
            booking_id=created_booking.id,
            balance_id=created_balance.id,
        )
        db_session.add(transaction)
        await db_session.commit()

        # 2. Выполняем GET запрос
        response = await client.get("/transactions/")

        assert response.status_code == 200
        data = response.json()

        # 3. Проверки
        assert len(data) >= 1
        # Проверяем, что наша транзакция есть в списке по ID пользователя
        assert any(t["user_id"] == created_landlord_user.id for t in data)

    async def test_get_transaction_by_id(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_landlord_user: User,
        created_booking: Booking,
        created_balance: Balance,
        sample_payment_data: dict[str, Any],
    ) -> None:
        """Test retrieving a specific transaction by ID."""
        transaction = Transaction(
            amount=sample_payment_data["amount"],
            transaction_type="booking_payment",
            user_id=created_landlord_user.id,
            booking_id=created_booking.id,
            balance_id=created_balance.id,
        )
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)

        response = await client.get(f"/transactions/{transaction.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == transaction.id
        assert data["amount"] == sample_payment_data["amount"]
        assert data["transaction_type"] == "booking_payment"

    async def test_get_transaction_not_found(self, client: AsyncClient) -> None:
        """Test retrieving a non-existent transaction."""
        response = await client.get("/transactions/99999")
        assert response.status_code == 404

    async def test_update_transaction(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_landlord_user: User,
        created_booking: Booking,
        created_balance: Balance,
        sample_payment_data: dict[str, Any],
    ) -> None:
        """Test updating a transaction."""
        transaction = Transaction(
            amount=sample_payment_data["amount"],
            transaction_type="booking_payment",
            user_id=created_landlord_user.id,
            booking_id=created_booking.id,
            balance_id=created_balance.id,
        )
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)

        # Валидный тип "refund" из вашего списка
        update_data = {"amount": 300.0, "transaction_type": "refund"}
        response = await client.patch(f"/transactions/{transaction.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 300.0
        assert data["transaction_type"] == "refund"

    async def test_delete_transaction(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_landlord_user: User,
        created_booking: Booking,
        created_balance: Balance,
        sample_payment_data: dict[str, Any],
    ) -> None:
        """Test deleting a transaction."""
        transaction = Transaction(
            amount=sample_payment_data["amount"],
            transaction_type="booking_payment",
            user_id=created_landlord_user.id,
            booking_id=created_booking.id,
            balance_id=created_balance.id,
        )
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)

        response = await client.delete(f"/transactions/{transaction.id}")
        assert response.status_code == 204

        # Verify deletion
        response = await client.get(f"/transactions/{transaction.id}")
        assert response.status_code == 404

    async def test_filter_transactions_by_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_landlord_user: User,
        created_booking: Booking,
        created_balance: Balance,
        sample_payment_data: dict[str, Any],
    ) -> None:
        """Test filtering transactions by user_id."""
        transaction = Transaction(
            amount=sample_payment_data["amount"],
            transaction_type="host_payout",
            user_id=created_landlord_user.id,
            booking_id=created_booking.id,
            balance_id=created_balance.id,
        )
        db_session.add(transaction)
        await db_session.commit()

        response = await client.get(f"/transactions/?user_id={created_landlord_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(t["user_id"] == created_landlord_user.id for t in data)

    async def test_filter_transactions_by_booking(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        created_landlord_user: User,
        created_booking: Booking,
        created_balance: Balance,
        sample_payment_data: dict[str, Any],
    ) -> None:
        """Test filtering transactions by booking_id."""
        transaction = Transaction(
            amount=sample_payment_data["amount"],
            transaction_type="booking_payment",
            user_id=created_landlord_user.id,
            booking_id=created_booking.id,
            balance_id=created_balance.id,
        )
        db_session.add(transaction)
        await db_session.commit()

        response = await client.get(f"/transactions/?booking_id={created_booking.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(t["booking_id"] == created_booking.id for t in data)

    async def test_transaction_types(
        self,
        client: AsyncClient,
        created_landlord_user: User,
        created_booking: Booking,
        created_balance: Balance,
    ) -> None:
        """Test creating transactions with different types."""
        from app.models.transaction import TransactionType
        
        # Список типов, которые мы реально поддерживаем в 2026 году
        types_to_test = [
            TransactionType.BOOKING_PAYMENT.value,
            TransactionType.HOST_PAYOUT.value,
            TransactionType.OWNER_DIVIDEND.value,
            TransactionType.INVESTOR_PAYOUT.value,
        ]
       
        for trans_type in types_to_test:
            data = {
            "amount": 100.0,
            "transaction_type": trans_type,
            "user_id": created_landlord_user.id,
            "booking_id": created_booking.id,
            "balance_id": created_balance.id,
        }
        response = await client.post("/transactions/", json=data)
        assert response.status_code == 201, f"Failed for type {trans_type}: {response.text}"
        assert response.json()["transaction_type"] == trans_type
