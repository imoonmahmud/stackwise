from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, ge=0)
    billing_period: Literal["monthly", "yearly", "one_time"] | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    is_free: bool = False
    description: str | None = None

class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, ge=0)
    billing_period: Literal["monthly", "yearly", "one_time"] | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_free: bool | None = None
    description: str | None = None

class PlanRead(BaseModel):
    id: int
    name: str
    price: Decimal | None
    billing_period: str | None
    currency: str
    is_free: bool
    description: str | None

    model_config = ConfigDict(from_attributes=True)