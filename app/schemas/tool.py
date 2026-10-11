from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from typing import Any
from pydantic import field_validator

class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120)
    short_description: str = Field(max_length=255)
    pricing_model: str | None = Field(default=None, max_length=30)
    has_free_plan: bool = False
    api_available: bool = False

class ToolRead(BaseModel):
    id: int
    name: str
    slug: str
    short_description: str | None
    created_at: datetime
    pricing_model: str | None = Field(default=None, max_length=30)
    has_free_plan: bool | None = Field(default=None)
    api_available: bool | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)

class ToolUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    short_description: str | None = Field(default=None, max_length=255)
    pricing_model: str | None = Field(default=None)
    has_free_plan: bool = Field(default=None)
    api_available: bool = Field(default=None)

    @field_validator('name', 'slug', 'short_description', mode='before')
    @classmethod
    def empty_string_to_none(cls, v:Any):
        if v == '' or v == 'string' or None:
            return None
        return v
        
