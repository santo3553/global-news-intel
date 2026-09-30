from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ArticleBase(BaseModel):
    source_id: str
    title: str = Field(..., max_length=512)
    url: str = Field(..., max_length=2048)
    canonical_url: Optional[str] = Field(None, max_length=2048)
    author: Optional[str] = Field(None, max_length=255)
    published_at: Optional[datetime] = None
    language: str = Field(default="en", max_length=10)
    cleaned_content: Optional[str] = None


class ArticleResponse(ArticleBase):
    id: str
    fetched_at: datetime
    content_hash: Optional[str] = None
    processing_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
