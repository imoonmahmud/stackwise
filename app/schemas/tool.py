from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120)
    short_description: str = Field(max_length=255)

class ToolRead(BaseModel):
    id: int
    name: str
    slug: str
    short_description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)