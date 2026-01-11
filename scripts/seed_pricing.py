import asyncio
import sys
import os
from datetime import date
from decimal import Decimal
from psycopg.types.range import Range

# Добавляем корень проекта в пути, если запускаем файл напрямую
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal # Импортируйте вашу фабрику сессий
from app.models import ApartmentAvailability

async def seed_pricing_rules():
    # Используем вашу фабрику сессий
    async with AsyncSessionLocal() as session:
        # Для теста возьмем apartment_id = 1 (убедитесь, что он есть в базе)
        apartment_id = 1 
        
        rules = [
            ApartmentAvailability(
                apartment_id=apartment_id,
                blocked_period=Range(date(2025, 12, 30), date(2026, 1, 5), bounds="[)"),
                custom_price=Decimal("12000.00"),
                min_stay_days=3,
                reason="Новогодние каникулы"
            ),
            ApartmentAvailability(
                apartment_id=apartment_id,
                blocked_period=Range(date(2026, 1, 15), date(2026, 1, 17), bounds="[)"),
                is_blocked=True,
                reason="Замена смесителя"
            )
        ]
        
        try:
            session.add_all(rules)
            await session.commit()
            print("Successfully seeded pricing rules!")
        except Exception as e:
            await session.rollback()
            print(f"Error during seeding: {e}")

if __name__ == "__main__":
    asyncio.run(seed_pricing_rules())
