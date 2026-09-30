import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.config import settings
from apps.api.app.models import Event, Article, EventArticle, Source
from ai.schemas.extraction import ExtractedEventData
from workers.embeddings.embedding_engine import cosine_similarity, EmbeddingEngine
from workers.clustering.signals import (
    compute_geographic_similarity,
    compute_temporal_similarity,
    compute_entity_similarity,
    compute_category_similarity,
    compute_composite_cluster_score
)

logger = logging.getLogger("gni.clusterer")


def ensure_utc(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class ClusteringDecision:
    def __init__(
        self,
        action: str,  # 'merged' or 'created'
        event_id: str,
        cluster_score: float = 1.0,
        similarity_breakdown: Optional[Dict[str, float]] = None
    ):
        self.action = action
        self.event_id = event_id
        self.cluster_score = cluster_score
        self.similarity_breakdown = similarity_breakdown or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "event_id": self.event_id,
            "cluster_score": self.cluster_score,
            "similarity_breakdown": self.similarity_breakdown
        }


class EventClusterer:
    """
    Core Multi-Signal Event Clustering and Dynamic Lifecycle Engine.
    Implements Section 14 & 15:
    Articles describing the same real-world event are grouped into ONE dynamic Event entity.
    """

    def __init__(
        self,
        threshold: Optional[float] = None,
        time_window_hours: Optional[int] = None
    ):
        self.threshold = threshold or settings.CLUSTER_SIMILARITY_THRESHOLD
        self.time_window_hours = time_window_hours or settings.MAX_CLUSTER_TIME_WINDOW_HOURS
        self.embedding_engine = EmbeddingEngine()

    async def cluster_article(
        self,
        session: AsyncSession,
        article: Article,
        extracted_data: ExtractedEventData
    ) -> ClusteringDecision:
        """
        Evaluates an article against active candidate events in the temporal window.
        Merges into existing event if threshold is met, otherwise initializes a new event.
        """
        now = datetime.now(timezone.utc)
        article_time = ensure_utc(article.published_at or now)

        # 1. Fetch candidate active events within the temporal window
        window_start = article_time - timedelta(hours=self.time_window_hours)
        window_end = article_time + timedelta(hours=self.time_window_hours)

        stmt = (
            select(Event)
            .options(
                selectinload(Event.article_associations).selectinload(EventArticle.article)
            )
            .where(
                Event.status.in_(["active", "developing"]),
                Event.last_updated_at >= window_start,
                Event.first_seen_at <= window_end
            )
        )
        res = await session.execute(stmt)
        candidate_events = res.scalars().all()

        best_score = -1.0
        best_event: Optional[Event] = None
        best_breakdown: Dict[str, float] = {}

        article_lat = extracted_data.location.latitude
        article_lng = extracted_data.location.longitude
        article_entities = {e.name.lower().strip() for e in extracted_data.entities}

        # 2. Score candidate events
        for event in candidate_events:
            # Semantic Similarity: compare against founding/linked articles' embeddings
            semantic_sim = 0.50
            if article.embedding and event.article_associations:
                sims = []
                for assoc in event.article_associations:
                    if assoc.article and assoc.article.embedding:
                        sims.append(cosine_similarity(article.embedding, assoc.article.embedding))
                if sims:
                    semantic_sim = max(sims)

            # Geographic Similarity
            geo_sim = compute_geographic_similarity(
                lat1=article_lat,
                lon1=article_lng,
                lat2=event.latitude,
                lon2=event.longitude
            )

            # Temporal Similarity
            temporal_sim = compute_temporal_similarity(
                time1=article_time,
                time2=event.last_updated_at,
                max_window_hours=self.time_window_hours
            )

            # Entity Similarity
            event_entities = set()
            for assoc in event.article_associations:
                if assoc.article and assoc.article.title:
                    # Collect tokens from existing event titles as proxy entity tokens
                    event_entities.update(assoc.article.title.lower().split())
            entity_sim = compute_entity_similarity(article_entities, event_entities)
            # If country matches, add baseline entity bonus
            if event.country and extracted_data.location.country:
                if event.country.lower() == extracted_data.location.country.lower():
                    entity_sim = max(entity_sim, 0.60)

            # Category Similarity
            cat_sim = compute_category_similarity(
                cat_a=extracted_data.category,
                cat_b=event.category,
                subcat_a=extracted_data.subcategory,
                subcat_b=event.subcategory
            )

            # Multi-signal composite score
            composite = compute_composite_cluster_score(
                semantic_sim=semantic_sim,
                geo_sim=geo_sim,
                entity_sim=entity_sim,
                temporal_sim=temporal_sim,
                category_sim=cat_sim
            )

            if composite > best_score:
                best_score = composite
                best_event = event
                best_breakdown = {
                    "semantic": semantic_sim,
                    "geographic": geo_sim,
                    "entity": entity_sim,
                    "temporal": temporal_sim,
                    "category": cat_sim,
                    "composite": composite
                }

        # 3. Decision: Merge vs Create New
        if best_event is not None and best_score >= self.threshold:
            # ----------------------------------------------------
            # MERGE INTO EXISTING EVENT
            # ----------------------------------------------------
            event = best_event
            rel_type = "corroborating"
            if "update" in article.title.lower() or "latest" in article.title.lower():
                rel_type = "update"

            # Create EventArticle association
            link = EventArticle(
                event_id=event.id,
                article_id=article.id,
                similarity_score=best_score,
                relationship_type=rel_type,
                created_at=now
            )
            session.add(link)

            # Update event lifecycle (Section 15)
            last_event_updated = ensure_utc(event.last_updated_at)
            if article_time > last_event_updated:
                event.last_updated_at = article_time
            else:
                event.last_updated_at = now

            # If new article brings higher precision location (e.g. city vs country), upgrade coordinates
            if extracted_data.location.precision in ("city", "exact") and event.city is None:
                if article_lat and article_lng:
                    event.latitude = article_lat
                    event.longitude = article_lng
                    event.city = extracted_data.location.city
                    event.admin_region = extracted_data.location.admin_region or event.admin_region
                    event.location_confidence = max(event.location_confidence, extracted_data.location.location_confidence)

            # Dynamically update source coverage and confidence
            article_count = len(event.article_associations) + 1
            event.source_coverage_score = min(10.0, event.source_coverage_score + 0.8)
            event.confidence_score = min(0.99, round(event.confidence_score + 0.05, 3))
            
            # Recalculate dynamic importance
            event.importance_score = min(
                10.0,
                round(
                    0.7 * event.importance_score + 0.3 * (
                        0.5 * extracted_data.human_impact_estimate + 0.5 * extracted_data.global_impact_estimate
                    ),
                    2
                )
            )

            article.processing_status = "clustered"
            await session.commit()

            logger.info(
                "Merged article [%s] into Event [%s] ('%s') score=%.2f",
                article.id, event.id, event.canonical_title[:40], best_score
            )
            return ClusteringDecision(
                action="merged",
                event_id=event.id,
                cluster_score=best_score,
                similarity_breakdown=best_breakdown
            )

        else:
            # ----------------------------------------------------
            # INITIALIZE NEW EVENT ENTITY
            # ----------------------------------------------------
            new_event_id = f"evt-{article.id[:12]}"
            summary_text = (
                "\n".join(f"* {c}" for c in extracted_data.claims)
                if extracted_data.claims
                else article.cleaned_content or article.title
            )

            new_event = Event(
                id=new_event_id,
                canonical_title=extracted_data.event_title or article.title,
                summary=summary_text,
                category=extracted_data.category,
                subcategory=extracted_data.subcategory,
                latitude=article_lat if article_lat is not None else 0.0,
                longitude=article_lng if article_lng is not None else 0.0,
                country=extracted_data.location.country,
                admin_region=extracted_data.location.admin_region,
                city=extracted_data.location.city,
                location_confidence=extracted_data.location.location_confidence,
                importance_score=round(0.5 * extracted_data.human_impact_estimate + 0.5 * extracted_data.global_impact_estimate, 2),
                confidence_score=extracted_data.confidence,
                human_impact_score=extracted_data.human_impact_estimate,
                global_impact_score=extracted_data.global_impact_estimate,
                novelty_score=round(extracted_data.novelty * 10.0, 2),
                development_velocity_score=5.0,
                source_coverage_score=2.0,
                first_seen_at=article_time,
                last_updated_at=article_time,
                status="active"
            )
            session.add(new_event)
            await session.flush()

            # Link founding article as primary
            link = EventArticle(
                event_id=new_event.id,
                article_id=article.id,
                similarity_score=1.0,
                relationship_type="primary",
                created_at=now
            )
            session.add(link)

            article.processing_status = "clustered"
            await session.commit()

            logger.info(
                "Created NEW Event [%s] ('%s') from article [%s]",
                new_event.id, new_event.canonical_title[:40], article.id
            )
            return ClusteringDecision(
                action="created",
                event_id=new_event.id,
                cluster_score=1.0,
                similarity_breakdown=best_breakdown
            )
