from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from psycopg.types.range import Range

from app.models import ApartmentAvailability
from app.services.pricing import PricingService


@pytest.mark.asyncio
async def test_calculate_total_cost_mixed_prices(
    db_session, created_apartment
):
    """Тест: расчет суммы, где часть дней обычные, а часть — с наценкой."""
    # 1. Установим базовую цену 5000
    created_apartment.price_per_night = Decimal("5000.00")
    await db_session.commit()

    # 2. Добавим правило: 2 и 3 января цена 10000
    rule = ApartmentAvailability(
        apartment_id=created_apartment.id,
        blocked_period=Range(date(2026, 1, 2), date(2026, 1, 4), bounds="[)"),
        custom_price=Decimal("10000.00")
    )
    db_session.add(rule)
    await db_session.commit()

    # 3. Считаем бронь с 1 по 5 января (4 ночи)
    # 1 янв (5000) + 2 янв (10000) + 3 янв (10000) + 4 янв (5000) = 30000
    total = await PricingService.calculate_booking_price(
        db_session, created_apartment.id, date(2026, 1, 1), date(2026, 1, 5)
    )

    assert total == Decimal("30000.00")

@pytest.mark.asyncio
async def test_min_stay_violation(db_session, created_apartment):
    """Тест: проверка нарушения минимального срока проживания."""
    rule = ApartmentAvailability(
        apartment_id=created_apartment.id,
        blocked_period=Range(date(2026, 2, 1), date(2026, 2, 10), bounds="[)"),
        min_stay_days=5
    )
    db_session.add(rule)
    await db_session.commit()

    # Пытаемся забронировать на 3 ночи, когда нужно 5
    with pytest.raises(HTTPException) as exc:
        await PricingService.calculate_booking_price(
            db_session, created_apartment.id, date(2026, 2, 1), date(2026, 2, 4)
        )
    assert exc.value.status_code == 400
    assert "минимум 5" in exc.value.detail

@pytest.mark.asyncio
async def test_blocked_period(db_session, created_apartment):
    """Тест: попытка расчета в заблокированные даты."""
    rule = ApartmentAvailability(
        apartment_id=created_apartment.id,
        blocked_period=Range(date(2026, 3, 1), date(2026, 3, 5), bounds="[)"),
        is_blocked=True
    )
    db_session.add(rule)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await PricingService.calculate_booking_price(
            db_session, created_apartment.id, date(2026, 3, 2), date(2026, 3, 3)
        )
    assert "заблокирован" in exc.value.detail

@pytest.mark.asyncio
async def test_calculate_custom_prices(db_session, created_apartment):
    # Устанавливаем базовую цену
    created_apartment.price_per_night = Decimal("5000.00")
    await db_session.commit()

    # Арендодатель ставит цену 12000 на 1-2 января
    rule = ApartmentAvailability(
        apartment_id=created_apartment.id,
        blocked_period=Range(date(2026, 1, 1), date(2026, 1, 3), bounds="[)"),
        custom_price=Decimal("12000.00")
    )
    db_session.add(rule)
    await db_session.commit()

    # Считаем стоимость с 1 по 3 января (2 ночи)
    total = await PricingService.calculate_booking_price(
        db_session, created_apartment.id, date(2026, 1, 1), date(2026, 1, 3)
    )
    assert total == Decimal("24000.00") # 12000 * 2

@pytest.mark.asyncio
async def test_blocked_dates_forbidden(db_session, created_apartment):
    # Арендодатель блокирует даты
    rule = ApartmentAvailability(
        apartment_id=created_apartment.id,
        blocked_period=Range(date(2026, 1, 10), date(2026, 1, 15), bounds="[)"),
        is_blocked=True,
        reason="Ремонт"
    )
    db_session.add(rule)
    await db_session.commit()

    # Пытаемся рассчитать цену на заблокированную дату
    with pytest.raises(HTTPException) as exc:
        await PricingService.calculate_booking_price(
            db_session, created_apartment.id, date(2026, 1, 12), date(2026, 1, 13)
        )
    assert exc.value.status_code == 400
    assert "заблокирован" in exc.value.detail.lower()

@pytest.mark.asyncio
async def test_min_stay_requirement(db_session, created_apartment):
    # Арендодатель ставит ограничение "минимум 3 ночи" на выходные
    rule = ApartmentAvailability(
        apartment_id=created_apartment.id,
        blocked_period=Range(date(2026, 1, 23), date(2026, 1, 26), bounds="[)"),
        min_stay_days=3
    )
    db_session.add(rule)
    await db_session.commit()

    # Пытаемся забронировать только на 2 ночи
    with pytest.raises(HTTPException) as exc:
        await PricingService.calculate_booking_price(
            db_session, created_apartment.id, date(2026, 1, 23), date(2026, 1, 25)
        )
    assert exc.value.status_code == 400
    assert "минимум 3 ночи" in exc.value.detail.lower()

