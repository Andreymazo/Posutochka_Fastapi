from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.owner_earning import OwnerEarning


class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    current_share: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="owner")
    owner_earnings: Mapped[list["OwnerEarning"]] = relationship(
        back_populates="owner_role", 
        cascade="all, delete-orphan"
    )
# class Owner(Base):
#     """Balance model - represents earnings from bookings."""

#     __tablename__ = "owners"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     created_at: Mapped[datetime] = mapped_column(server_default=func.now())
#     updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

#     # user_id теперь уникален, так как у каждого User может быть только 1 роль Owner
#     user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False)
#     # Relationships
#     # user: Mapped["User"] = relationship(back_populates="owner") # Убрал, т.к. User импортируется

#     current_share: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0)
#     is_active: Mapped[bool] = mapped_column(default=True)
    
#     # Связь с историей выплат
#     # !!! ИЗМЕНИЛ back_populates на "owner_role" чтобы избежать конфликта имени user в OwnerEarning
#     owner_earnings: Mapped[list["OwnerEarning"]] = relationship(back_populates="owner_role", cascade="all, delete-orphan")
   