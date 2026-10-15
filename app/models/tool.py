from datetime import UTC, datetime

from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.category import Category
from app.models.tool_category import tool_categories
from app.models.feature import Feature
from app.models.tool_feature import tool_features
from app.models.pricing_plan import PricingPlan
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

    pricing_model: Mapped[str | None] = mapped_column(String(30), nullable=True)
    has_free_plan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    api_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary=tool_categories,
        back_populates="tools"
    )

    features: Mapped[list["Feature"]] = relationship(
        "Feature",
        secondary=tool_features,
        back_populates="tools"
    )

    pricing_plans: Mapped[list["PricingPlan"]] = relationship(
        "PricingPlan", 
        back_populates="tool", 
        cascade="all, delete-orphan", 
        order_by=PricingPlan.price
    )
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)




