"""Tests for Transaction API endpoints."""

import pytest
from typing import Any
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
            transaction_type="booking_income", 
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
            transaction_type="booking_income",
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
        transaction_types = [
            "booking_payment",
            "booking_income",
            "platform_commission",
            "refund",
            "withdrawal",
        ]

        for trans_type in transaction_types:
            data = {
                "amount": 100.0,
                "transaction_type": trans_type,
                "user_id": created_landlord_user.id,
                "booking_id": created_booking.id,
                "balance_id": created_balance.id,
            }
            response = await client.post("/transactions/", json=data)
            assert response.status_code == 201
            assert response.json()["transaction_type"] == trans_type



# """Tests for Transaction API endpoints."""

# from typing import Any

# from fastapi.testclient import TestClient
# from sqlalchemy.orm import Session

# from app.models import Balance, Booking, Transaction, User


# class TestTransactionEndpoints:
#     """Tests for transaction CRUD operations."""

#     def test_create_transaction(
#         self,
#         client: TestClient,
#         created_user: User,
#         created_booking: Booking,
#         created_balance: Balance,
#         sample_transaction_data: dict[str, Any],
#     ) -> None:
#         """Test creating a new transaction."""
#         data = {
#             **sample_transaction_data,
#             "user_id": created_user.id,
#             "booking_id": created_booking.id,
#             "balance_id": created_balance.id,
#         }
#         response = client.post("/transactions/", json=data)
#         assert response.status_code == 201
#         assert response.json()["amount"] == sample_transaction_data["amount"]
#         assert response.json()["transaction_type"] == sample_transaction_data["transaction_type"]
#         assert response.json()["user_id"] == created_user.id
#         assert response.json()["booking_id"] == created_booking.id
#         assert response.json()["balance_id"] == created_balance.id

#     def test_get_transactions(
#         self,
#         client: TestClient,
#         db_session: Session,
#         created_user: User,
#         created_booking: Booking,
#         created_balance: Balance,
#         sample_transaction_data: dict[str, Any],
#     ) -> None:
#         """Test retrieving all transactions."""
#         transaction = Transaction(
#             amount=sample_transaction_data["amount"],
#             transaction_type=sample_transaction_data["transaction_type"],
#             user_id=created_user.id,
#             booking_id=created_booking.id,
#             balance_id=created_balance.id,
#         )
#         db_session.add(transaction)
#         db_session.commit()

#         response = client.get("/transactions/")
#         assert response.status_code == 200
#         assert len(response.json()) >= 1



    # def test_get_transaction_by_id(
    #     self,
    #     client: TestClient,
    #     db_session: Session,
    #     created_user: User,
    #     created_booking: Booking,
    #     created_balance: Balance,
    #     sample_transaction_data: dict[str, Any],
    # ) -> None:
    #     """Test retrieving a specific transaction by ID."""
    #     transaction = Transaction(
    #         amount=sample_transaction_data["amount"],
    #         transaction_type=sample_transaction_data["transaction_type"],
    #         user_id=created_user.id,
    #         booking_id=created_booking.id,
    #         balance_id=created_balance.id,
    #     )
    #     db_session.add(transaction)
    #     db_session.commit()
    #     db_session.refresh(transaction)

    #     response = client.get(f"/transactions/{transaction.id}")
    #     assert response.status_code == 200
    #     assert response.json()["id"] == transaction.id
    #     assert response.json()["amount"] == sample_transaction_data["amount"]
    #     assert response.json()["transaction_type"] == sample_transaction_data["transaction_type"]

    # def test_get_transaction_not_found(self, client: TestClient) -> None:
    #     """Test retrieving a non-existent transaction."""
    #     response = client.get("/transactions/99999")
    #     assert response.status_code == 404

    # def test_update_transaction(
    #     self,
    #     client: TestClient,
    #     db_session: Session,
    #     created_user: User,
    #     created_booking: Booking,
    #     created_balance: Balance,
    #     sample_transaction_data: dict[str, Any],
    # ) -> None:
    #     """Test updating a transaction."""
    #     transaction = Transaction(
    #         amount=sample_transaction_data["amount"],
    #         transaction_type=sample_transaction_data["transaction_type"],
    #         user_id=created_user.id,
    #         booking_id=created_booking.id,
    #         balance_id=created_balance.id,
    #     )
    #     db_session.add(transaction)
    #     db_session.commit()
    #     db_session.refresh(transaction)

    #     update_data = {"amount": 300.0, "transaction_type": "refund"}
    #     response = client.patch(f"/transactions/{transaction.id}", json=update_data)
    #     assert response.status_code == 200
    #     assert response.json()["amount"] == 300.0
    #     assert response.json()["transaction_type"] == "refund"

    # def test_delete_transaction(
    #     self,
    #     client: TestClient,
    #     db_session: Session,
    #     created_user: User,
    #     created_booking: Booking,
    #     created_balance: Balance,
    #     sample_transaction_data: dict[str, Any],
    # ) -> None:
    #     """Test deleting a transaction."""
    #     transaction = Transaction(
    #         amount=sample_transaction_data["amount"],
    #         transaction_type=sample_transaction_data["transaction_type"],
    #         user_id=created_user.id,
    #         booking_id=created_booking.id,
    #         balance_id=created_balance.id,
    #     )
    #     db_session.add(transaction)
    #     db_session.commit()
    #     db_session.refresh(transaction)

    #     response = client.delete(f"/transactions/{transaction.id}")
    #     assert response.status_code == 204

    #     # Verify deletion
    #     response = client.get(f"/transactions/{transaction.id}")
    #     assert response.status_code == 404

    # def test_filter_transactions_by_user(
    #     self,
    #     client: TestClient,
    #     db_session: Session,
    #     created_user: User,
    #     created_booking: Booking,
    #     created_balance: Balance,
    #     sample_transaction_data: dict[str, Any],
    # ) -> None:
    #     """Test filtering transactions by user_id."""
    #     transaction = Transaction(
    #         amount=sample_transaction_data["amount"],
    #         transaction_type=sample_transaction_data["transaction_type"],
    #         user_id=created_user.id,
    #         booking_id=created_booking.id,
    #         balance_id=created_balance.id,
    #     )
    #     db_session.add(transaction)
    #     db_session.commit()

    #     response = client.get(f"/transactions/?user_id={created_user.id}")
    #     assert response.status_code == 200
    #     assert len(response.json()) >= 1
    #     assert all(t["user_id"] == created_user.id for t in response.json())

    # def test_filter_transactions_by_booking(
    #     self,
    #     client: TestClient,
    #     db_session: Session,
    #     created_user: User,
    #     created_booking: Booking,
    #     created_balance: Balance,
    #     sample_transaction_data: dict[str, Any],
    # ) -> None:
    #     """Test filtering transactions by booking_id."""
    #     transaction = Transaction(
    #         amount=sample_transaction_data["amount"],
    #         transaction_type=sample_transaction_data["transaction_type"],
    #         user_id=created_user.id,
    #         booking_id=created_booking.id,
    #         balance_id=created_balance.id,
    #     )
    #     db_session.add(transaction)
    #     db_session.commit()

    #     response = client.get(f"/transactions/?booking_id={created_booking.id}")
    #     assert response.status_code == 200
    #     assert len(response.json()) >= 1
    #     assert all(t["booking_id"] == created_booking.id for t in response.json())

    # def test_transaction_types(
    #     self,
    #     client: TestClient,
    #     created_user: User,
    #     created_booking: Booking,
    #     created_balance: Balance,
    # ) -> None:
    #     """Test creating transactions with different types."""
    #     transaction_types = [
    #         "booking_payment",
    #         "booking_income",
    #         "platform_commission",
    #         "refund",
    #         "withdrawal",
    #     ]

    #     for trans_type in transaction_types:
    #         data = {
    #             "amount": 100.0,
    #             "transaction_type": trans_type,
    #             "user_id": created_user.id,
    #             "booking_id": created_booking.id,
    #             "balance_id": created_balance.id,
    #         }
    #         response = client.post("/transactions/", json=data)
    #         assert response.status_code == 201
    #         assert response.json()["transaction_type"] == trans_type
