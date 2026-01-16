import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi import HTTPException
from app.services.availability_service import AvailabilityService
from app.models.apartmentavailability import ApartmentAvailability

@pytest.mark.asyncio
async def test_create_availability_overlap_raises_error(db_session, created_apartment):
    """Тест на ошибку 400 при наложении периодов."""
    start = date(2026, 7, 1)
    end = date(2026, 7, 10)
    
    # Создаем первое правило
    await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, start, end
    )
    
    # Пытаемся создать второе, пересекающееся (с 5 по 15 число)
    with pytest.raises(HTTPException) as exc:
        await AvailabilityService.create_blocked_period(
            db_session, created_apartment.id, start + timedelta(days=5), end + timedelta(days=5)
        )
    
    assert exc.value.status_code == 400
    assert "Пересекающееся правило" in exc.value.detail

@pytest.mark.asyncio
async def test_get_rule_by_id_not_found(db_session):
    """Тест на ошибку 404 при поиске несуществующего правила."""
    with pytest.raises(HTTPException) as exc:
        await AvailabilityService.get_availability_rule_by_id(db_session, 9999)
    
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_update_availability_rule_success(db_session, created_apartment):
    """Тест успешного обновления дат и параметров."""
    # 1. Создаем
    rule = await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, date(2026, 8, 1), date(2026, 8, 5)
    )
    
    # 2. Обновляем (только дату окончания и цену)
    new_end = date(2026, 8, 10)
    updated = await AvailabilityService.update_availability_rule(
        db_session, 
        rule.id, 
        end_date=new_end, 
        custom_price=Decimal("5000.00"),
        reason="Праздники"
    )
    
    assert updated.blocked_period.upper == new_end
    assert updated.custom_price == Decimal("5000.00")
    assert updated.reason == "Праздники"

@pytest.mark.asyncio
async def test_delete_availability_rule(db_session, created_apartment):
    """Тест удаления правила."""
    # 1. Создаем
    rule = await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, date(2026, 9, 1), date(2026, 9, 2)
    )
    
    # 2. Удаляем
    await AvailabilityService.delete_availability_rule(db_session, rule.id)
    
    # 3. Проверяем, что его нет
    with pytest.raises(HTTPException) as exc:
        await AvailabilityService.get_availability_rule_by_id(db_session, rule.id)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_get_availability_rules_list(db_session, created_apartment):
    """Тест получения списка правил с пагинацией."""
    # Создаем 2 правила
    await AvailabilityService.create_blocked_period(db_session, created_apartment.id, date(2026, 1, 1), date(2026, 1, 2))
    await AvailabilityService.create_blocked_period(db_session, created_apartment.id, date(2026, 1, 5), date(2026, 1, 6))
    
    rules = await AvailabilityService.get_availability_rules(db_session, created_apartment.id, limit=1)
    assert len(rules) == 1
@pytest.mark.asyncio
async def test_update_availability_rule_partial_dates_and_none_fields(db_session, created_apartment):
    """Тест для покрытия веток, где обновляется только начало даты или поля равны None."""
    # 1. Создаем правило
    start = date(2026, 12, 1)
    end = date(2026, 12, 10)
    rule = await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, start, end, custom_price=Decimal("100")
    )
    
    # 2. Обновляем только start_date (сработает ветка current_end)
    # И НЕ передаем остальные поля (проверка веток 'if field is not None')
    new_start = date(2026, 12, 2)
    updated = await AvailabilityService.update_availability_rule(
        db_session, 
        rule.id, 
        start_date=new_start
        # остальные поля None по умолчанию
    )
    
    assert updated.blocked_period.lower == new_start
    assert updated.blocked_period.upper == end # осталось прежним
    assert updated.custom_price == Decimal("100") # не затерлось в None
@pytest.mark.asyncio
async def test_update_availability_rule_missing_branches(db_session, created_apartment):
    """Закрываем оставшиеся ветки: только end_date, is_blocked и min_stay_days."""
    # 1. Создаем базу
    start = date(2026, 5, 1)
    end = date(2026, 5, 5)
    rule = await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, start, end, is_blocked=True, min_stay_days=2
    )
    
    # 2. Обновляем то, что еще не трогали в тестах:
    # Передаем end_date (чтобы сработал branch 171->181 для start_date)
    # Передаем is_blocked и min_stay_days (строки 184 и 188)
    updated = await AvailabilityService.update_availability_rule(
        db_session, 
        rule.id, 
        end_date=date(2026, 5, 6),
        is_blocked=False,
        min_stay_days=5
    )
    
    assert updated.blocked_period.lower == start  # Проверка, что начало не изменилось
    assert updated.is_blocked is False
    assert updated.min_stay_days == 5
@pytest.mark.asyncio
async def test_update_only_end_date_branch(db_session, created_apartment):
    """Закрываем ветку 171->181: передаем только end_date."""
    # 1. Исходные данные
    original_start = date(2026, 10, 1)
    original_end = date(2026, 10, 5)
    rule = await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, original_start, original_end
    )
    
    # 2. Обновляем ТОЛЬКО дату окончания
    # start_date будет None, сработает ветка new_start = current_start
    new_end = date(2026, 10, 7)
    updated = await AvailabilityService.update_availability_rule(
        db_session, 
        rule.id, 
        end_date=new_end
    )
    
    assert updated.blocked_period.lower == original_start
    assert updated.blocked_period.upper == new_end

@pytest.mark.asyncio
async def test_update_availability_all_date_combinations(db_session, created_apartment):
    """Финальный тест для закрытия ветки 171->181: проверяем все комбинации дат."""
    # 1. Создаем исходное правило
    rule = await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, date(2026, 1, 10), date(2026, 1, 20)
    )

    # Комбинация А: Обновляем только начало (start_date=True, end_date=None)
    # Это закроет одну сторону ветки
    await AvailabilityService.update_availability_rule(
        db_session, rule.id, start_date=date(2026, 1, 11)
    )

    # Комбинация Б: Обновляем только конец (start_date=None, end_date=True)
    # Это закроет вторую сторону ветки (current_start)
    await AvailabilityService.update_availability_rule(
        db_session, rule.id, end_date=date(2026, 1, 25)
    )

    # Комбинация В: Обновляем оба (start_date=True, end_date=True)
    res = await AvailabilityService.update_availability_rule(
        db_session, rule.id, start_date=date(2026, 1, 5), end_date=date(2026, 1, 15)
    )

    assert res.blocked_period.lower == date(2026, 1, 5)
    assert res.blocked_period.upper == date(2026, 1, 15)
@pytest.mark.asyncio
async def test_update_without_dates_branch(db_session, created_apartment):
    """Закрываем BrPart 171->181: вызываем update, где start_date и end_date оба None."""
    # 1. Создаем правило
    original_start = date(2026, 11, 1)
    original_end = date(2026, 11, 5)
    rule = await AvailabilityService.create_blocked_period(
        db_session, created_apartment.id, original_start, original_end, custom_price=Decimal("100")
    )
    
    # 2. Обновляем ТОЛЬКО цену (даты остаются None)
    # Это заставит coverage увидеть, что условие 'if start_date or end_date' может быть ложным
    updated = await AvailabilityService.update_availability_rule(
        db_session, 
        rule.id, 
        custom_price=Decimal("200")
    )
    
    assert updated.custom_price == Decimal("200")
    assert updated.blocked_period.lower == original_start
    assert updated.blocked_period.upper == original_end
# pytest --cov=app.services.availability_service --cov-report=term-missing tests/test_availability_service.py