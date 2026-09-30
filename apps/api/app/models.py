import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    TypeDecorator,
)
from sqlalchemy.orm import relationship

from apps.api.app.database import Base, is_sqlite


def utc_now():
    return datetime.now(timezone.utc)


def generate_uuid():
    return str(uuid.uuid4())


# Custom Geometry representation that uses PostGIS Geometry when available, or Text (WKT/GeoJSON) on SQLite
class SpatialPoint(TypeDecorator):
    """
    Platform-independent Spatial Point.
    Uses PostGIS Geometry(POINT, 4326) on PostgreSQL, and Text (WKT: 'POINT(lon lat)') on SQLite.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from geoalchemy2 import Geometry
                return dialect.type_descriptor(Geometry(geometry_type="POINT", srid=4326))
            except ImportError:
                return dialect.type_descriptor(Text)
        return dialect.type_descriptor(Text)


class Source(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    feed_url = Column(String(1024), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False, default="rss")  # rss, api, scraper
    country = Column(String(10), nullable=True)  # ISO 2-letter or 3-letter code
    language = Column(String(10), nullable=False, default="en")
    reliability_score = Column(Float, nullable=False, default=0.7)  # 0.0 to 1.0
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")


class Article(Base):
    __tablename__ = "articles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    canonical_url = Column(String(2048), nullable=True, index=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    fetched_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    language = Column(String(10), nullable=False, default="en")
    raw_content = Column(Text, nullable=True)
    cleaned_content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256
    title_hash = Column(String(64), nullable=True, index=True)    # SHA-256
    embedding = Column(JSON, nullable=True)  # Vector embedding stored as float list
    processing_status = Column(String(50), nullable=False, default="pending", index=True)  # pending, normalized, extracted, clustered, failed
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    source = relationship("Source", back_populates="articles")
    event_associations = relationship("EventArticle", back_populates="article", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    canonical_title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)  # natural_disaster, politics, security, economy, etc.
    subcategory = Column(String(100), nullable=True)
    
    # Geographic Data
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    geometry = Column(SpatialPoint, nullable=True)
    country = Column(String(100), nullable=True, index=True)
    admin_region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    location_confidence = Column(Float, nullable=False, default=1.0)

    # Multi-dimensional Importance and Confidence Scores
    importance_score = Column(Float, nullable=False, default=5.0, index=True)  # 0.0 - 10.0
    confidence_score = Column(Float, nullable=False, default=0.5)  # 0.0 - 1.0
    human_impact_score = Column(Float, nullable=False, default=0.0)
    global_impact_score = Column(Float, nullable=False, default=0.0)
    economic_impact_score = Column(Float, nullable=False, default=0.0)
    political_impact_score = Column(Float, nullable=False, default=0.0)
    novelty_score = Column(Float, nullable=False, default=0.0)
    development_velocity_score = Column(Float, nullable=False, default=0.0)
    source_coverage_score = Column(Float, nullable=False, default=0.0)

    # Lifecycle
    first_seen_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    last_updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active", index=True)  # active, developing, resolved, archived
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    article_associations = relationship("EventArticle", back_populates="event", cascade="all, delete-orphan")
    entity_associations = relationship("EventEntity", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_events_lat_lng", "latitude", "longitude"),
        Index("idx_events_importance_first_seen", "importance_score", "first_seen_at"),
    )


class EventArticle(Base):
    __tablename__ = "event_articles"

    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    article_id = Column(String(36), ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    similarity_score = Column(Float, nullable=False, default=1.0)
    relationship_type = Column(String(50), nullable=False, default="corroborating")  # primary, corroborating, update, tangential
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    event = relationship("Event", back_populates="article_associations")
    article = relationship("Article", back_populates="event_associations")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # person, organization, location, country, concept
    normalized_name = Column(String(255), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    country = Column(String(100), nullable=True)

    # Relationships
    event_associations = relationship("EventEntity", back_populates="entity", cascade="all, delete-orphan")


class EventEntity(Base):
    __tablename__ = "event_entities"

    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    entity_id = Column(String(36), ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    event = relationship("Event", back_populates="entity_associations")
    entity = relationship("Entity", back_populates="event_associations")
