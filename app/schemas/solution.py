from datetime import datetime
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ToolBrief(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)

class StepCreate(BaseModel):
    tool_id: int
    role: Annotated[str, Field(min_length=1, max_length=50)]
    note: str | None = None

class StepRead(BaseModel):
    step_order: int
    role: str
    note: str | None
    tool: ToolBrief

    model_config = ConfigDict(from_attributes=True)

class SolutionCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=150)]
    slug: Annotated[str, Field(min_length=1, max_length=160)]
    short_description: str | None = Field(default=None, max_length=255)
    description: str | None = None
    steps: list[StepCreate] = Field(min_length=1)

class SolutionUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=150)
    slug: str | None = Field(default=None, max_length=160)
    short_description: str | None = Field(default=None, max_length=255)
    description: str | None = None
    steps: list[StepCreate] | None = None

    @field_validator("steps", mode="before")
    @classmethod
    def reject_null_steps(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("steps cannot be null")
        return value

class SolutionListItem(BaseModel):
    id: int
    title: str
    slug: str
    short_description: str | None

    model_config = ConfigDict(from_attributes=True)

class SolutionRead(SolutionListItem):
    description: str | None
    created_at: datetime
    steps: list[StepRead]

    model_config = ConfigDict(from_attributes=True)