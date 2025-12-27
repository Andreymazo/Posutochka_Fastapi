from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.apartment import Apartment


class Photo(Base):
    """Photo model - represents an apartment photo."""

    __tablename__ = "photo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    apartment_id: Mapped[int] = mapped_column(ForeignKey("apartment.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    apartment: Mapped["Apartment"] = relationship(back_populates="photos")

    def __repr__(self) -> str:
        return f"Photo(id={self.id}, apartment_id={self.apartment_id}, url='{self.url}')"
