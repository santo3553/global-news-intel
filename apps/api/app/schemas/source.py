from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SourceBase(BaseModel):
    name: str = Field(..., max_length=255)
    domain: str = Field(..., max_length=255)
    feed_url: str = Field(..., max_length=1024)
    source_type: str = Field(default="rss", max_length=50)
    country: Optional[str] = Field(None, max_length=10)
    language: str = Field(default="en", max_length=10)
    reliability_score: float = Field(default=0.7, ge=0.0, le=1.0)
    active: bool = True


class SourceCreate(SourceBase):
    pass


class SourceResponse(SourceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
