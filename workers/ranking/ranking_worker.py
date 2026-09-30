import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.models import Event, EventArticle, Article, Source
from workers.ranking.impact_scorer import (
    compute_event_importance,
    calculate_geographic_scope,
    calculate_source_coverage_score,
    calculate_development_velocity,
    ImpactScores
)
from workers.ranking.confidence_scorer import compute_multi_source_confidence

logger = logging.getLogger("gni.ranking.worker")


class EventRankingWorker:
    """
    Orchestrates multi-dimensional impact scoring and multi-source confidence calculation.
    Implements Sections 16, 17, and 18.
    """

    @classmethod
    async def update_event_ranking(
        cls,
        session: AsyncSession,
        event: Event
    ) -> Dict[str, Any]:
        """
        Recomputes all 8 impact dimensions and multi-source confidence for an event,
        persisting the updated scores to the database.
        """
        # Ensure event articles and their sources are fully loaded
        stmt = (
            select(EventArticle)
            .options(
                selectinload(EventArticle.article).selectinload(Article.source)
            )
            .where(EventArticle.event_id == event.id)
        )
        res = await session.execute(stmt)
        associations = res.scalars().all()

        articles = [a.article for a in associations if a.article]
        article_count = max(1, len(articles))

        # Collect source information for multi-source confidence & coverage
        sources_info: List[Dict[str, Any]] = []
        for a in articles:
            if a.source:
                sources_info.append({
                    "source_id": a.source.id,
                    "domain": a.source.domain,
                    "source_name": a.source.name,
                    "country": a.source.country,
                    "reliability_score": a.source.reliability_score
                })
            else:
                sources_info.append({
                    "source_id": a.source_id,
                    "domain": "wire.generic",
                    "reliability_score": 0.75
                })

        # 1. Geographic Scope
        geo_score = calculate_geographic_scope(
            city=event.city,
            admin_region=event.admin_region,
            country=event.country,
            category=event.category
        )

        # 2. Source Coverage Score
        unique_sources = {s.get("domain") or s.get("source_id") for s in sources_info}
        coverage_score = calculate_source_coverage_score(len(unique_sources))

        # 3. Development Velocity
        now = datetime.now(timezone.utc)
        velocity_score = calculate_development_velocity(
            article_count=article_count,
            first_seen_at=event.first_seen_at,
            last_updated_at=event.last_updated_at,
            now=now
        )

        # 4. Multi-Impact Scores (Human, Global, Economic, Political, Novelty)
        # Use existing baseline scores, updated by incoming articles
        human_score = event.human_impact_score if event.human_impact_score > 0 else 5.0
        global_score = event.global_impact_score if event.global_impact_score > 0 else 5.0
        econ_score = event.economic_impact_score if event.economic_impact_score > 0 else 3.0
        pol_score = event.political_impact_score if event.political_impact_score > 0 else 4.0
        novel_score = event.novelty_score if event.novelty_score > 0 else 6.0

        # In natural disasters or conflicts, scale human score with coverage
        if event.category in ("natural_disaster", "security", "conflict") and len(unique_sources) >= 2:
            human_score = min(10.0, human_score + 0.5)

        # Compute full 8-dimension weighted importance
        impact_result: ImpactScores = compute_event_importance(
            human_impact=human_score,
            global_impact=global_score,
            geographic_impact=geo_score,
            economic_impact=econ_score,
            political_impact=pol_score,
            novelty=novel_score,
            velocity=velocity_score,
            source_coverage=coverage_score
        )

        # 5. Multi-Source Confidence Model
        confidence_result = compute_multi_source_confidence(
            sources_info=sources_info,
            location_confidence=event.location_confidence,
            contradiction_detected=False
        )

        # 6. Apply updates to the Event entity
        event.human_impact_score = impact_result.human_impact
        event.global_impact_score = impact_result.global_impact
        event.economic_impact_score = impact_result.economic_impact
        event.political_impact_score = impact_result.political_impact
        event.novelty_score = impact_result.novelty
        event.development_velocity_score = impact_result.velocity
        event.source_coverage_score = impact_result.source_coverage
        event.importance_score = impact_result.importance_score
        event.confidence_score = confidence_result["confidence_score"]

        logger.info(
            "Ranked Event [%s] ('%s'): Importance=%.2f, Confidence=%.3f, Velocity=%.2f, Sources=%d",
            event.id, event.canonical_title[:35],
            event.importance_score, event.confidence_score,
            event.development_velocity_score, len(unique_sources)
        )

        return {
            "event_id": event.id,
            "importance_score": event.importance_score,
            "confidence_score": event.confidence_score,
            "impact_breakdown": impact_result.to_dict(),
            "confidence_breakdown": confidence_result
        }

    @classmethod
    async def batch_decay_events(
        cls,
        session: AsyncSession,
        max_events: int = 50
    ) -> int:
        """
        Applies time decay to development velocity and transitions old events
        from active -> developing -> resolved.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Event)
            .where(Event.status.in_(["active", "developing"]))
            .limit(max_events)
        )
        res = await session.execute(stmt)
        events = res.scalars().all()

        updated_count = 0
        for event in events:
            last_up = event.last_updated_at
            if last_up.tzinfo is None:
                last_up = last_up.replace(tzinfo=timezone.utc)
            
            hours_idle = (now - last_up).total_seconds() / 3600.0

            # Decay velocity
            if hours_idle > 2.0:
                event.development_velocity_score = round(
                    max(0.0, event.development_velocity_score * 0.85),
                    2
                )
                # Recalculate importance with reduced velocity
                impact = compute_event_importance(
                    human_impact=event.human_impact_score,
                    global_impact=event.global_impact_score,
                    geographic_impact=3.0,
                    economic_impact=event.economic_impact_score,
                    political_impact=event.political_impact_score,
                    novelty=event.novelty_score,
                    velocity=event.development_velocity_score,
                    source_coverage=event.source_coverage_score
                )
                event.importance_score = impact.importance_score

            # Transition status
            if hours_idle > 48.0 and event.status == "developing":
                event.status = "resolved"
            elif hours_idle > 12.0 and event.status == "active":
                event.status = "developing"

            updated_count += 1

        if updated_count > 0:
            await session.commit()

        return updated_count
