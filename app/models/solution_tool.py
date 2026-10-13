from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
if TYPE_CHECKING:
    from app.models.solution import Solution
    from app.models.tool import Tool

class SolutionTool(Base):
    __tablename__ = "solution_tools"

    id: Mapped[int] = mapped_column(primary_key=True)
    solution_id: Mapped[int] = mapped_column(ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id", ondelete="RESTRICT"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("solution_id", "step_order", name="uq_solution_step_order"),
    )

    solution: Mapped["Solution"] = relationship("Solution", back_populates="steps")
    tool: Mapped["Tool"] = relationship("Tool")