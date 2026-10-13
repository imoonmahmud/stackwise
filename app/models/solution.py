from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
if TYPE_CHECKING:
    from app.models.solution_tool import SolutionTool

class Solution(Base):
    __tablename__ = "solutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    short_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    steps: Mapped[list["SolutionTool"]] = relationship(
        back_populates="solution",
        cascade="all, delete-orphan",
        order_by="SolutionTool.step_order"
    )