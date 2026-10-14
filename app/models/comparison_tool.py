from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.comparison import Comparison
    from app.models.tool import Tool

class ComparisonTool(Base):
    __tablename__ = "comparison_tools"

    comparison_id: Mapped[int] = mapped_column(ForeignKey("comparisons.id", ondelete="CASCADE"), primary_key=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id", ondelete="RESTRICT"), primary_key=True, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("comparison_id", "position", name="uq_comparison_position"),
    )

    comparison: Mapped["Comparison"] = relationship("Comparison", back_populates="tools")
    tool: Mapped["Tool"] = relationship("Tool")