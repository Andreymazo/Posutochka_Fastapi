
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# Импортируем ВСЕ нужные модели
from app.models import Booking, Owner, Investor, Transaction, Balance, OwnerEarning
# Явно импортируем Enum для использования в коде
from app.models.transaction import TransactionType 
from sqlalchemy.orm import selectinload

class FinanceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.COMMISSION_RATE = Decimal("0.15") 
        self.TAX_RATE = Decimal("0.06")        

    async def process_booking_completion(self, booking_id: int):
        """Точка входа: распределяет деньги после завершения брони."""
        
        # ИСПОЛЬЗУЕМ selectinload для всех связей, к которым будем обращаться
        stmt = (
            select(Booking)
            .options(
                selectinload(Booking.payments),
                selectinload(Booking.landlord)
            )
            .where(Booking.id == booking_id)
        )
        result = await self.session.execute(stmt)
        
        booking = result.scalar_one()
        
        if not booking.is_fully_paid:
            raise ValueError("Бронирование не оплачено полностью")

        # 1. Расчеты
        total_price = booking.cost
        commission = total_price * self.COMMISSION_RATE
        landlord_amount = total_price - commission
        tax_amount = commission * self.TAX_RATE
        net_profit = commission - tax_amount

        # 2. Выплата Арендодателю (Landlord) - ИСПОЛЬЗУЕМ TransactionType
        await self._add_money(
            user_id=booking.landlord.user_id,
            amount=landlord_amount,
            booking_id=booking.id,
            tx_type=TransactionType.HOST_PAYOUT # <-- Используется здесь
        )

        # 3. Распределение прибыли (Инвесторы и Владельцы)
        investor_pool = net_profit * Decimal("0.40")
        remaining_profit = net_profit - investor_pool

        await self._manage_investor_payouts(investor_pool, booking.id)
        await self._manage_owner_payouts(remaining_profit, booking.id)

    async def _manage_investor_payouts(self, pool: Decimal, booking_id: int):
        """Использование модели Investor"""
        res = await self.session.execute(select(Investor))
        investors = res.scalars().all()
        
        if not investors:
            return

        share_per_inv = pool / len(investors)
        for inv in investors:
            inv.returned_amount += share_per_inv 
            
            await self._add_money(
                user_id=inv.user_id, 
                amount=share_per_inv, 
                booking_id=booking_id, 
                tx_type=TransactionType.INVESTOR_PAYOUT # <-- Используется здесь
            )

    async def _manage_owner_payouts(self, profit: Decimal, booking_id: int):
        """Использование моделей Owner и OwnerEarning"""
        res = await self.session.execute(select(Owner).where(Owner.is_active == True))
        owners = res.scalars().all()

        for owner in owners:
            owner_amount = profit * owner.current_share
            if owner_amount > 0:
                earning = OwnerEarning(
                    amount=owner_amount,
                    applied_share=owner.current_share,
                    user_id=owner.user_id,
                    owner_id=owner.id,
                    booking_id=booking_id
                )
                self.session.add(earning)

                await self._add_money(
                    user_id=owner.user_id, 
                    amount=owner_amount, 
                    booking_id=booking_id, 
                    tx_type=TransactionType.OWNER_DIVIDEND # <-- Используется здесь
                )

    # async def _add_money(self, user_id: int, amount: Decimal, booking_id: int, tx_type: TransactionType):
    #     """Низкоуровневое начисление на баланс с записью транзакции."""
    #     res = await self.session.execute(select(Balance).where(Balance.user_id == user_id))
    #     balance = res.scalar_one()

    #     transaction = Transaction(
    #         amount=amount,
    #         # Тип транзакции, который мы пробрасываем через параметр
    #         transaction_type=tx_type, 
    #         user_id=user_id,
    #         booking_id=booking_id,
    #         balance_id=balance.id
    #     )
    #     self.session.add(transaction)

    #     balance.current_balance += amount
    async def _add_money(self, user_id: int, amount: Decimal, booking_id: int, tx_type: TransactionType):
        """Низкоуровневое начисление на баланс с записью транзакции."""
        
        # 1. Пытаемся найти существующий баланс
        res = await self.session.execute(
            select(Balance).where(Balance.user_id == user_id)
        )
        balance = res.scalar_one_or_none()

        # 2. Если баланса нет — создаем новую запись
        if balance is None:
            balance = Balance(
                user_id=user_id,
                current_balance=Decimal("0.00")
            )
            self.session.add(balance)
            # Делаем flush, чтобы БД присвоила ID балансу, который нужен для Transaction.balance_id
            await self.session.flush()

        # 3. Создаем транзакцию
        transaction = Transaction(
            amount=amount,
            transaction_type=tx_type, 
            user_id=user_id,
            booking_id=booking_id,
            balance_id=balance.id
        )
        self.session.add(transaction)

        # 4. Обновляем итоговую сумму в модели Balance
        # Поле называется current_balance согласно вашему описанию модели
        balance.current_balance += amount


# from decimal import Decimal
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# # Импортируем ВСЕ нужные модели
# from app.models import Booking, Owner, Investor, Transaction, Balance, OwnerEarning
# from app.models.transaction import TransactionType

# class FinanceService:
#     def __init__(self, session: AsyncSession):
#         self.session = session
#         self.COMMISSION_RATE = Decimal("0.15") 
#         self.TAX_RATE = Decimal("0.06")        

#     async def process_booking_completion(self, booking_id: int):
#         """Точка входа: распределяет деньги после завершения брони."""
#         result = await self.session.execute(
#             select(Booking).where(Booking.id == booking_id)
#         )
#         booking = result.scalar_one()

#         if not booking.is_fully_paid:
#             raise ValueError("Бронирование не оплачено")

#         # 1. Расчеты
#         total_price = booking.cost
#         commission = total_price * self.COMMISSION_RATE
#         landlord_amount = total_price - commission
#         tax_amount = commission * self.TAX_RATE
#         net_profit = commission - tax_amount

#         # 2. Выплата Арендодателю (Landlord)
#         await self._add_money(
#             user_id=booking.landlord.user_id,
#             amount=landlord_amount,
#             booking_id=booking.id,
#             tx_type=TransactionType.HOST_PAYOUT
#         )

#         # 3. Распределение прибыли (Инвесторы и Владельцы)
#         # Допустим, 40% прибыли идет инвесторам, 60% — владельцам
#         investor_pool = net_profit * Decimal("0.40")
#         remaining_profit = net_profit - investor_pool

#         await self._manage_investor_payouts(investor_pool, booking.id)
#         await self._manage_owner_payouts(remaining_profit, booking.id)

#     async def _manage_investor_payouts(self, pool: Decimal, booking_id: int):
#         """Использование модели Investor"""
#         res = await self.session.execute(select(Investor))
#         investors = res.scalars().all()
        
#         if not investors:
#             return

#         share_per_inv = pool / len(investors)
#         for inv in investors:
#             # Обновляем состояние модели Investor (сколько ему уже вернулось)
#             inv.returned_amount += share_per_inv 
            
#             await self._add_money(
#                 user_id=inv.user_id, 
#                 amount=share_per_inv, 
#                 booking_id=booking_id, 
#                 tx_type=TransactionType.INVESTOR_PAYOUT
#             )

#     async def _manage_owner_payouts(self, profit: Decimal, booking_id: int):
#         """Использование моделей Owner и OwnerEarning"""
#         # Берем только активных владельцев
#         res = await self.session.execute(select(Owner).where(Owner.is_active == True))
#         owners = res.scalars().all()

#         for owner in owners:
#             owner_amount = profit * owner.current_share
#             if owner_amount > 0:
#                 # 1. Создаем запись в историю OwnerEarning
#                 earning = OwnerEarning(
#                     amount=owner_amount,
#                     applied_share=owner.current_share,
#                     user_id=owner.user_id,
#                     owner_id=owner.id,
#                     booking_id=booking_id
#                 )
#                 self.session.add(earning)

#                 # 2. Начисляем реальные деньги на баланс
#                 await self._add_money(
#                     user_id=owner.user_id, 
#                     amount=owner_amount, 
#                     booking_id=booking_id, 
#                     tx_type=TransactionType.OWNER_DIVIDEND
#                 )

#     async def _add_money(self, user_id: int, amount: Decimal, booking_id: int, tx_type: TransactionType):
#         """Использование моделей Balance и Transaction"""
#         res = await self.session.execute(select(Balance).where(Balance.user_id == user_id))
#         balance = res.scalar_one()

#         # Создаем финансовую транзакцию
#         transaction = Transaction(
#             amount=amount,
#             transaction_type=tx_type,
#             user_id=user_id,
#             booking_id=booking_id,
#             balance_id=balance.id
#         )
#         self.session.add(transaction)

#         # Обновляем кошелек
#         balance.current_balance += amount
