from datetime import datetime, UTC
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Numeric, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.tool import Tool

class PricingPlan(Base):
    __tablename__ = 'pricing_plans'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey('tools.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    billing_period: Mapped[str] = mapped_column(String(20), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    tool = relationship("Tool", back_populates="pricing_plans")