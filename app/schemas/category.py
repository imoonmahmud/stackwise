from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None)


class CategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)