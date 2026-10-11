from sqlalchemy import Column, ForeignKey, Integer, Table
from app.database import Base

tool_categories = Table(
    "tool_categories",
    Base.metadata,
    Column("tool_id", Integer, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)