# app/models/message.py
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy import ForeignKey, Text, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models import User, Booking

class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Контекст чата — бронирование
    # При удалении брони — удаляем сообщение физически
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("booking.id", ondelete="CASCADE"), index=True
    )
    
    # Отправитель. При удалении юзера — оставляем сообщение, но зануляем автора 
    # (или блокируем удаление юзера, пока есть сообщения)
    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), 
        nullable=True
    )
    # Содержание
    text: Mapped[str] = mapped_column(Text)
    
    # Telegram интеграция
    # Храним ID сообщения в TG, чтобы работал Reply-to-Message
    tg_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Пометка, прочитано ли сообщение (полезно для личного кабинета)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    tg_user_id: Mapped[int | None] = mapped_column(sa.BigInteger, unique=True, nullable=True)
    # Связи
    booking: Mapped["Booking"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(back_populates="sent_messages")
