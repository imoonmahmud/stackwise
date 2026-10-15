from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, HttpUrl, Field, ConfigDict, field_validator

class LinkCreate(BaseModel):
    network: str = Field(..., min_length=1, max_length=50)
    affiliate_url: HttpUrl
    commission_type: Literal["percent", "fixed", "recurring"] | None = None
    commission_value: Decimal | None = Field(default=None, ge=Decimal("0"))
    is_active: bool = True


class LinkUpdate(BaseModel):
    network: str | None = Field(default=None, min_length=1, max_length=50)
    affiliate_url: HttpUrl | None = None
    commission_type: Literal["percent", "fixed", "recurring"] | None = None
    commission_value: Decimal | None = Field(default=None, ge=Decimal("0"))
    is_active: bool | None = None

    @field_validator("network", "affiliate_url", "is_active", mode="before")
    @classmethod
    def prevent_explicit_nulls(cls, v, info):
        if v is None:
            raise ValueError(f"Field '{info.field_name}' cannot be explicitly set to null.")
        return v


class LinkRead(BaseModel):
    id: int
    tool_id: int
    network: str
    affiliate_url: str
    commission_type: str | None = None
    commission_value: Decimal | None = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DayClickStat(BaseModel):
    date: date
    clicks: int


class SourceClickStat(BaseModel):
    utm_source: str | None
    clicks: int


class ClickStats(BaseModel):
    total: int
    unique_visitors: int
    by_day: list[DayClickStat]
    by_source: list[SourceClickStat]