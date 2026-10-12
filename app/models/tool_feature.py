from sqlalchemy import Column, ForeignKey, Integer, Table
from app.database import Base

tool_features = Table(
    'tool_features',
    Base.metadata,
    Column("tool_id", Integer, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
    Column("feature_id", Integer, ForeignKey("features.id", ondelete="CASCADE"), primary_key=True)
)