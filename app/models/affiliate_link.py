from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base

class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True)
    network: Mapped[str] = mapped_column(String(50), nullable=False)
    affiliate_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    commission_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    commission_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("uq_one_active_link_per_tool", "tool_id", unique=True, postgresql_where=text("is_active")),
    )