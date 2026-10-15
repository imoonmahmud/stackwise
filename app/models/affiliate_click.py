from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database import Base

class AffiliateClick(Base):
    __tablename__ = "affiliate_clicks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    link_id: Mapped[int | None] = mapped_column(ForeignKey("affiliate_links.id", ondelete="SET NULL"), nullable=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_clicks_tool_time", "tool_id", "clicked_at"),
    )