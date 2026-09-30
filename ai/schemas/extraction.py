from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ExtractedLocation(BaseModel):
    name: str = Field(..., description="Canonical location name (e.g. 'Kyushu, Japan')")
    country: Optional[str] = Field(None, description="Country name or ISO code (e.g. 'Japan')")
    admin_region: Optional[str] = Field(None, description="State, province, or prefecture (e.g. 'Kyushu')")
    city: Optional[str] = Field(None, description="City or municipality (e.g. 'Miyazaki')")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="WGS84 Latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="WGS84 Longitude")
    precision: str = Field(
        default="country",
        description="Location granularity: 'exact', 'city', 'region', 'country', or 'global'"
    )
    location_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence that the event occurred at this specific location (avoids false precision)"
    )


class ExtractedEntity(BaseModel):
    name: str = Field(..., description="Entity name (e.g. 'Japan Meteorological Agency')")
    type: str = Field(..., description="Entity type: 'country', 'location', 'person', 'organization', or 'concept'")


class ExtractedEventData(BaseModel):
    event_title: str = Field(..., max_length=512, description="Concise, factual title of the real-world event")
    category: str = Field(
        ...,
        description="Primary category: 'natural_disaster', 'politics', 'security', 'economy', 'science', 'health', 'environment', 'society'"
    )
    subcategory: Optional[str] = Field(None, description="Specific subcategory (e.g. 'earthquake', 'diplomacy', 'trade')")
    location: ExtractedLocation = Field(..., description="Geographic location of the event")
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted named entities")
    claims: List[str] = Field(default_factory=list, description="Core factual claims reported in the story")
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Estimated severity/damage or disruption (0.0 to 1.0)")
    novelty: float = Field(default=0.5, ge=0.0, le=1.0, description="How novel or surprising this development is (0.0 to 1.0)")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in the factual accuracy of the report")
    human_impact_estimate: float = Field(default=5.0, ge=0.0, le=10.0, description="Estimated direct impact on human life and safety")
    global_impact_estimate: float = Field(default=5.0, ge=0.0, le=10.0, description="Estimated international or systemic significance")

    model_config = ConfigDict(from_attributes=True)
