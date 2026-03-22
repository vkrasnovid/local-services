import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.master import MasterProfile


class Category(BaseModel):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )

    # Relationships
    master_profiles: Mapped[List["MasterProfile"]] = relationship(
        "MasterProfile", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category {self.id} {self.name}>"
