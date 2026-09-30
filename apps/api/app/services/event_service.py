import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.models import Event, EventArticle, Article, Entity, EventEntity
from workers.clustering.signals import haversine_distance_km

logger = logging.getLogger("gni.services.events")


class EventService:
    """
    Query, filter, and management service for Events.
    Supports bounding-box queries, radial proximity searches, and importance ranking.
    """

    @staticmethod
    def parse_bbox(bbox_str: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Parses 'min_lng,min_lat,max_lng,max_lat' bounding box string.
        Returns (min_lng, min_lat, max_lng, max_lat) or None.
        """
        try:
            parts = [float(p.strip()) for p in bbox_str.split(",")]
            if len(parts) == 4:
                return (parts[0], parts[1], parts[2], parts[3])
        except Exception:
            pass
        return None

    @classmethod
    async def list_events(
        cls,
        session: AsyncSession,
        bbox: Optional[str] = None,
        category: Optional[str] = None,
        country: Optional[str] = None,
        min_importance: Optional[float] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        stmt = select(Event).options(
            selectinload(Event.article_associations)
        )

        conditions = []

        # 1. Geographic Bounding Box Filter
        if bbox:
            parsed = cls.parse_bbox(bbox)
            if parsed:
                min_lng, min_lat, max_lng, max_lat = parsed
                conditions.append(Event.latitude >= min_lat)
                conditions.append(Event.latitude <= max_lat)
                conditions.append(Event.longitude >= min_lng)
                conditions.append(Event.longitude <= max_lng)

        # 2. Category & Country Filter
        if category:
            conditions.append(Event.category == category.lower().strip())
        if country:
            conditions.append(Event.country == country.strip())

        # 3. Importance Threshold
        if min_importance is not None:
            conditions.append(Event.importance_score >= min_importance)

        # 4. Status Filter
        if status:
            conditions.append(Event.status == status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Event.importance_score.desc(), Event.last_updated_at.desc()).offset(offset).limit(limit)

        result = await session.execute(stmt)
        events = result.scalars().all()

        output = []
        for evt in events:
            evt_dict = {
                "id": evt.id,
                "canonical_title": evt.canonical_title,
                "summary": evt.summary,
                "category": evt.category,
                "subcategory": evt.subcategory,
                "latitude": evt.latitude,
                "longitude": evt.longitude,
                "country": evt.country,
                "admin_region": evt.admin_region,
                "city": evt.city,
                "location_confidence": evt.location_confidence,
                "importance_score": evt.importance_score,
                "confidence_score": evt.confidence_score,
                "human_impact_score": evt.human_impact_score,
                "global_impact_score": evt.global_impact_score,
                "economic_impact_score": evt.economic_impact_score,
                "political_impact_score": evt.political_impact_score,
                "novelty_score": evt.novelty_score,
                "development_velocity_score": evt.development_velocity_score,
                "source_coverage_score": evt.source_coverage_score,
                "first_seen_at": evt.first_seen_at,
                "last_updated_at": evt.last_updated_at,
                "status": evt.status,
                "article_count": len(evt.article_associations)
            }
            output.append(evt_dict)

        return output

    @classmethod
    async def get_event_detail(
        cls,
        session: AsyncSession,
        event_id: str
    ) -> Optional[Dict[str, Any]]:
        stmt = (
            select(Event)
            .options(
                selectinload(Event.article_associations).selectinload(EventArticle.article),
                selectinload(Event.entity_associations).selectinload(EventEntity.entity)
            )
            .where(Event.id == event_id)
        )
        res = await session.execute(stmt)
        evt = res.scalar_one_or_none()
        if not evt:
            return None

        articles_list = []
        for assoc in evt.article_associations:
            art = assoc.article
            if art:
                articles_list.append({
                    "id": art.id,
                    "source_id": art.source_id,
                    "title": art.title,
                    "url": art.url,
                    "canonical_url": art.canonical_url,
                    "author": art.author,
                    "published_at": art.published_at,
                    "fetched_at": art.fetched_at,
                    "language": art.language,
                    "cleaned_content": art.cleaned_content,
                    "processing_status": art.processing_status,
                    "created_at": art.created_at,
                    "relationship_type": assoc.relationship_type,
                    "similarity_score": assoc.similarity_score
                })

        entities_list = []
        for e_assoc in evt.entity_associations:
            if e_assoc.entity:
                entities_list.append({
                    "id": e_assoc.entity.id,
                    "name": e_assoc.entity.name,
                    "entity_type": e_assoc.entity.entity_type,
                    "country": e_assoc.entity.country
                })

        return {
            "id": evt.id,
            "canonical_title": evt.canonical_title,
            "summary": evt.summary,
            "category": evt.category,
            "subcategory": evt.subcategory,
            "latitude": evt.latitude,
            "longitude": evt.longitude,
            "country": evt.country,
            "admin_region": evt.admin_region,
            "city": evt.city,
            "location_confidence": evt.location_confidence,
            "importance_score": evt.importance_score,
            "confidence_score": evt.confidence_score,
            "human_impact_score": evt.human_impact_score,
            "global_impact_score": evt.global_impact_score,
            "economic_impact_score": evt.economic_impact_score,
            "political_impact_score": evt.political_impact_score,
            "novelty_score": evt.novelty_score,
            "development_velocity_score": evt.development_velocity_score,
            "source_coverage_score": evt.source_coverage_score,
            "first_seen_at": evt.first_seen_at,
            "last_updated_at": evt.last_updated_at,
            "status": evt.status,
            "article_count": len(articles_list),
            "articles": articles_list,
            "entities": entities_list
        }

    @classmethod
    async def get_nearby_events(
        cls,
        session: AsyncSession,
        lat: float,
        lng: float,
        radius_km: float = 300.0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Finds events within radius_km using great-circle Haversine distance.
        """
        all_events = await cls.list_events(session, limit=200)
        nearby = []

        for evt in all_events:
            e_lat = evt["latitude"]
            e_lng = evt["longitude"]
            dist_km = haversine_distance_km(lat, lng, e_lat, e_lng)
            if dist_km <= radius_km:
                evt_copy = dict(evt)
                evt_copy["distance_km"] = round(dist_km, 1)
                nearby.append(evt_copy)

        nearby.sort(key=lambda x: x["distance_km"])
        return nearby[:limit]
