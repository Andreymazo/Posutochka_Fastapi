import pytest
from httpx import AsyncClient
from starlette import status
from app.models.payment import Payment

@pytest.mark.asyncio
async def test_payments_full_lifecycle(
    client: AsyncClient, 
    db_session, 
    created_booking  # Используем твою существующую фикстуру
):
    """
    Тест покрывает все эндпоинты payments.py:
    POST, GET (list), GET (one), PATCH, DELETE + 404 ошибки.
    """
    
    # 1. POST /payments/ (Создание)
    payment_data = {
        "booking_id": created_booking.id,
        "amount": 500.0,
        "payment_status": "pending"
    }
    response = await client.post("/payments/", json=payment_data)
    assert response.status_code == status.HTTP_201_CREATED
    created_payment = response.json()
    payment_id = created_payment["id"]

    # 2. GET /payments/ (Список с фильтром)
    # Покрывает строки 17-22 (фильтрация по booking_id)
    response = await client.get("/payments/", params={"booking_id": created_booking.id})
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["id"] == payment_id

    # 3. GET /payments/{payment_id} (Успех и 404)
    # Покрывает строки 28-33
    response = await client.get(f"/payments/{payment_id}")
    assert response.status_code == 200
    
    response = await client.get("/payments/999999")
    assert response.status_code == 404

    # 4. PATCH /payments/{payment_id} (Обновление статуса)
    # Покрывает строки 55-70 (включая логику .value для Enum)
    update_data = {"payment_status": "paid", "amount": 600.0}
    response = await client.patch(f"/payments/{payment_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["payment_status"] == "paid"
    assert response.json()["amount"] == 600.0
    
    # Проверка 404 для метода PATCH (строка 59)
    resp_patch_404 = await client.patch("/payments/999999", json={"amount": 100})
    assert resp_patch_404.status_code == 404

    # Можно также добавить для DELETE и GET, чтобы точно закрыть все ветки 'if not payment'
    resp_get_404 = await client.get("/payments/999999")
    assert resp_get_404.status_code == 404

    resp_delete_404 = await client.delete("/payments/999999")
    assert resp_delete_404.status_code == 404

    # 5. DELETE /payments/{payment_id} (Удаление и 404)
    # Покрывает строки 76-83
    response = await client.delete(f"/payments/{payment_id}")
    assert response.status_code == 204
    
    response = await client.delete(f"/payments/{payment_id}") # Повторно для 404
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_payments_extra_branches(client: AsyncClient, db_session, created_booking):
    # 1. Закрываем ветку "18->20" (GET без фильтра booking_id)
    # Когда мы НЕ передаем params, срабатывает логика 'if booking_id' = False
    response = await client.get("/payments/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # 2. Сначала создадим платеж для тестов PATCH
    payment_data = {"booking_id": created_booking.id, "amount": 100, "payment_status": "pending"}
    resp = await client.post("/payments/", json=payment_data)
    payment_id = resp.json()["id"]

    # 3. Закрываем ветку "62->65" (PATCH без изменения статуса)
    # Мы меняем только сумму. Блок 'if update_data.get("payment_status")' будет пропущен
    response = await client.patch(f"/payments/{payment_id}", json={"amount": 200.0})
    assert response.status_code == 200
    assert response.json()["amount"] == 200.0
    assert response.json()["payment_status"] == "pending" # Статус не должен измениться

