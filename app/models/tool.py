from datetime import UTC, datetime

from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    short_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    pricing_model: Mapped[str] = mapped_column(String(30), nullable=True)
    has_free_plan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    api_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)