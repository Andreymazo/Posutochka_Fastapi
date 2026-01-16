import enum
from decimal import Decimal
from sqlalchemy import Numeric, ForeignKey, Enum, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy.sql import func
from typing import Optional
from app.models import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class InvestorType(enum.Enum):
    """Enumeration for investor types."""
    # Получает инвестиции обратно до выплаты дивидендов владельцам
    RETURNABLE = "returnable"
    # Получает только дивиденды после владельцев (если что-то останется)
    EQUITY = "equity"



class Investor(Base):
    """Investor model - tracks investor status and investment type."""

    __tablename__ = "investors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    investment_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False, default=Decimal("0.00")
    )
    returned_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False, default=Decimal("0.00")
    )
    # Использование Enum для типа инвестора
    investor_type: Mapped[InvestorType] = mapped_column(
        Enum(InvestorType), nullable=False, default=InvestorType.EQUITY
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="investor")
    
    @property
    def is_investment_returned(self) -> bool:
        """Check if the full investment has been returned."""
        return self.returned_amount >= self.investment_amount
    @property
    def remaining_investment(self) -> Decimal:
        """Вычисляет остаток долга перед инвестором."""
        return max(Decimal("0.00"), self.investment_amount - self.returned_amount)
    
    
    @classmethod
    async def has_unreturned_investments(cls, session) -> bool:
        """Проверяет, есть ли в системе инвесторы, которым еще не вернули деньги."""
        from sqlalchemy import select
    
        stmt = select(cls).filter(
            cls.investor_type == InvestorType.RETURNABLE,
            cls.returned_amount < cls.investment_amount
        )
        result = await session.execute(stmt)
        return result.first() is not None