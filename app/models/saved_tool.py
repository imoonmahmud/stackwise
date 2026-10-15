from sqlalchemy import Column, ForeignKey, Integer, DateTime, Table, CheckConstraint, func
from app.database import Base

saved_tools = Table(
    "saved_tools",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("tool_id", Integer, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True, index=True, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)