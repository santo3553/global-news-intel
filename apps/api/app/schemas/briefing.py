from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BriefingItem(BaseModel):
    event_id: str
    title: str
    category: str
    location: str
    importance: float
    confidence: float
    velocity: float
    summary: str
    key_takeaway: str


class IntelligenceBriefingResponse(BaseModel):
    generated_at: datetime
    executive_summary: str
    total_events_analyzed: int
    breaking_alerts: List[BriefingItem] = []
    critical_geopolitical: List[BriefingItem] = []
    humanitarian_hazards: List[BriefingItem] = []
    economic_disruptions: List[BriefingItem] = []

    model_config = ConfigDict(from_attributes=True)


class TimelineEntry(BaseModel):
    article_id: str
    title: str
    source_name: str
    source_domain: str
    url: Optional[str] = None
    canonical_url: Optional[str] = None
    published_at: Optional[datetime] = None
    relationship_type: str  # primary, corroborating, update
    similarity_score: float
    excerpt: Optional[str] = None


class EventTimelineResponse(BaseModel):
    event_id: str
    canonical_title: str
    first_seen_at: datetime
    last_updated_at: datetime
    total_articles: int
    timeline: List[TimelineEntry] = []

    model_config = ConfigDict(from_attributes=True)
