from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.solution import ToolBrief

class ComparisonCreate(BaseModel):
    tool_ids: list[int] = Field(min_length=2, max_length=4)
    summary: str | None = None

    @field_validator("tool_ids", mode="before")
    @classmethod
    def validate_tool_ids(cls, value: Any) -> Any:
        if not isinstance(value, list):
            raise ValueError("tool_ids must be a list")
        if len(value) != len(set(value)):
            raise ValueError("Duplicate tool IDs are not allowed in comparisons")
        return value

class ComparisonRow(BaseModel):
    label: str
    values: list[str | bool | None]

class ComparisonRead(BaseModel):
    slug: str
    summary: str | None
    created_at: datetime
    tools: list[ToolBrief]
    rows: list[ComparisonRow]

    model_config = ConfigDict(from_attributes=True)

class ComparisonListItem(BaseModel):
    slug: str
    summary: str | None
    tool_count: int

    model_config = ConfigDict(from_attributes=True)