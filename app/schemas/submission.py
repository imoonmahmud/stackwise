from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field, ConfigDict, field_validator
import re

class SubmissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=120)
    website_url: HttpUrl
    short_description: str | None = Field(default=None, max_length=255)
    pricing_model: str | None = Field(default=None, max_length=30)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase letters, digits, and hyphens")
        return v


class SubmissionRead(BaseModel):
    id: int
    submitted_by_id: int | None = None
    name: str
    slug: str
    website_url: str
    short_description: str | None = None
    pricing_model: str | None = None
    note: str | None = None
    status: str
    reviewer_id: int | None = None
    review_note: str | None = None
    reviewed_at: datetime | None = None
    tool_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewReject(BaseModel):
    review_note: str = Field(..., min_length=3, max_length=1000)