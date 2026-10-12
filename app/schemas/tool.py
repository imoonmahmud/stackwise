from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any

from app.schemas.category import CategoryRead
from app.schemas.feature import FeatureRead

class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120)
    short_description: str | None = Field(default=None, max_length=255)
    pricing_model: str | None = Field(default=None, max_length=30)
    has_free_plan: bool = False
    api_available: bool = False
    category_ids: list[int] = Field(default_factory=list)
    feature_ids: list[int] = Field(default_factory=list)



class ToolRead(BaseModel):
    id: int
    name: str
    slug: str
    short_description: str | None
    created_at: datetime
    pricing_model: str | None = Field(default=None, max_length=30)
    has_free_plan: bool | None = Field(default=None)
    api_available: bool | None = Field(default=None)
    categories: list[CategoryRead] = []
    features: list[FeatureRead] = []

    model_config = ConfigDict(from_attributes=True)

class ToolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    short_description: str | None = Field(default=None, max_length=255)
    pricing_model: str | None = Field(default=None, max_length=30)
    has_free_plan: bool | None = Field(default=None)
    api_available: bool | None = Field(default=None)
    category_ids: list[int] | None = Field(default=None)
    feature_ids: list[int] | None = Field(default=None)

    @field_validator('category_ids', mode='before')
    @classmethod
    def validate_category_ids(cls, v: Any):
        if v is None:
            raise ValueError("category_ids cannot be null")
        return v

    @field_validator('feature_ids', mode='before')
    @classmethod
    def validate_feature_ids(cls, v: Any):
        if v is None:
            raise ValueError("feature_ids cannot be null")
        return v

    model_config = ConfigDict(from_attributes=True)