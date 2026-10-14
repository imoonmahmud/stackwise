from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.comparison_tool import ComparisonTool

class Comparison(Base):
    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tools: Mapped[list["ComparisonTool"]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
        order_by="ComparisonTool.position"
    )