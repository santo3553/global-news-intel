from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from apps.api.app.schemas.article import ArticleResponse


class EventBase(BaseModel):
    canonical_title: str = Field(..., max_length=512)
    summary: str
    category: str = Field(..., max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    country: Optional[str] = None
    admin_region: Optional[str] = None
    city: Optional[str] = None
    location_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    importance_score: float = Field(default=5.0, ge=0.0, le=10.0)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)


class EventResponse(EventBase):
    id: str
    human_impact_score: float
    global_impact_score: float
    economic_impact_score: float
    political_impact_score: float
    novelty_score: float
    development_velocity_score: float
    source_coverage_score: float
    first_seen_at: datetime
    last_updated_at: datetime
    status: str
    article_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class EventDetailResponse(EventResponse):
    articles: List[ArticleResponse] = []
    entities: List[dict] = []
