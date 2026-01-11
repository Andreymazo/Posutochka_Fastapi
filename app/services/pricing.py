from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Apartment, ApartmentAvailability
from psycopg.types.range import Range
from fastapi import HTTPException

class PricingService:
    @staticmethod
    async def calculate_booking_price(
        db: AsyncSession, 
        apartment_id: int, 
        start_date: date, 
        end_date: date
    ) -> Decimal:
        """
        Рассчитывает итоговую стоимость проживания с учетом календаря цен и блокировок.
        """
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Дата заезда должна быть раньше даты выезда")

        # 1. Получаем базовые данные апартамента (для price_per_night)
        apt_result = await db.execute(select(Apartment).filter(Apartment.id == apartment_id))
        apartment = apt_result.scalar_one_or_none()
        if not apartment:
            raise HTTPException(status_code=404, detail="Апартамент не найден")

        total_nights = (end_date - start_date).days

        # 2. Создаем диапазон искомого бронирования для запроса к БД
        # [) - включительно начало, исключительно конец
        booking_range = Range(start_date, end_date, bounds="[)")

        # 3. Ищем все правила доступности, перекрывающие наш диапазон
        query = select(ApartmentAvailability).where(
            and_(
                ApartmentAvailability.apartment_id == apartment_id,
                ApartmentAvailability.blocked_period.overlaps(booking_range)
            )
        )
        result = await db.execute(query)
        availability_rules = result.scalars().all()

        # 4. Построение карты цен и ограничений по дням
        # Инициализируем каждый день базовой ценой и минимальным сроком (например, 1 день)
        daily_data: Dict[date, Dict[str, Any]] = {
            start_date + timedelta(days=i): {
                "price": apartment.price_per_night,
                "blocked": False,
                "min_stay": 1 # Базовый min_stay, будет перезаписан правилами
            } 
            for i in range(total_nights)
        }

        # 5. Накладываем custom_price, блокировки и min_stay из правил
        for rule in availability_rules:
            # Проходим по всем дням бронирования и применяем правила, если день входит в диапазон правила
            for day in daily_data.keys():
                if day in rule.blocked_period:
                    if rule.is_blocked:
                        # Если день заблокирован, выбрасываем исключение сразу
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Апартамент заблокирован для бронирования на дату: {day} (Причина: {rule.reason or 'не указана'})"
                        )
                    
                    if rule.custom_price is not None:
                        daily_data[day]["price"] = rule.custom_price
                    
                    # Обновляем min_stay_days, если найдено более высокое ограничение
                    if rule.min_stay_days > daily_data[day]["min_stay"]:
                        daily_data[day]["min_stay"] = rule.min_stay_days

        # 6. Финальная проверка min_stay_days по всем примененным правилам
        max_required_min_stay = max(d["min_stay"] for d in daily_data.values())
        if total_nights < max_required_min_stay:
            raise HTTPException(
                status_code=400, 
                detail=f"На выбранные даты действует ограничение: минимум {max_required_min_stay} ночи"
            )

        # 7. Суммируем стоимость
        total_cost = sum(day["price"] for day in daily_data.values())
        return Decimal(total_cost).quantize(Decimal("1.00"))
