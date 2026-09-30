import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.models import Event, EventArticle, Article
from apps.api.app.schemas.briefing import (
    IntelligenceBriefingResponse,
    BriefingItem,
    EventTimelineResponse,
    TimelineEntry
)

logger = logging.getLogger("gni.services.briefing")


class BriefingService:
    """
    Synthesizes real-time intelligence briefings and chronological event timelines.
    Implements Section 22 and 23.
    """

    @classmethod
    async def generate_briefing(
        cls,
        session: AsyncSession,
        limit_per_section: int = 4
    ) -> IntelligenceBriefingResponse:
        """
        Answers 'What should I read right now?' by synthesizing the highest-impact,
        high-velocity, and strategic global events into an executive intelligence memo.
        """
        now = datetime.now(timezone.utc)

        # Query top active events ordered by importance
        stmt = (
            select(Event)
            .options(selectinload(Event.article_associations))
            .where(Event.status.in_(["active", "developing"]))
            .order_by(Event.importance_score.desc(), Event.development_velocity_score.desc())
            .limit(25)
        )
        res = await session.execute(stmt)
        events = res.scalars().all()

        breaking_alerts: List[BriefingItem] = []
        geopolitical: List[BriefingItem] = []
        hazards: List[BriefingItem] = []
        economic: List[BriefingItem] = []

        def to_briefing_item(evt: Event) -> BriefingItem:
            loc = evt.city or evt.country or "Global"
            if evt.city and evt.country:
                loc = f"{evt.city}, {evt.country}"

            key_takeaway = (
                f"Significant {evt.category.replace('_', ' ')} incident with importance "
                f"{evt.importance_score:.1f}/10 corroborated across {len(evt.article_associations)} reports."
            )

            return BriefingItem(
                event_id=evt.id,
                title=evt.canonical_title,
                category=evt.category,
                location=loc,
                importance=evt.importance_score,
                confidence=evt.confidence_score,
                velocity=evt.development_velocity_score,
                summary=evt.summary[:240] + ("..." if len(evt.summary) > 240 else ""),
                key_takeaway=key_takeaway
            )

        for evt in events:
            item = to_briefing_item(evt)

            # Breaking alerts: rapid incoming reports
            if evt.development_velocity_score >= 6.0 and len(breaking_alerts) < limit_per_section:
                breaking_alerts.append(item)

            # Geopolitical: high global or political impact
            if (evt.category == "politics" or evt.global_impact_score >= 6.0) and len(geopolitical) < limit_per_section:
                geopolitical.append(item)

            # Hazards / Natural Disasters / Conflict
            if (evt.category in ("natural_disaster", "security", "conflict") or evt.human_impact_score >= 6.0) and len(hazards) < limit_per_section:
                hazards.append(item)

            # Economic disruptions
            if (evt.category == "economy" or evt.economic_impact_score >= 5.5) and len(economic) < limit_per_section:
                economic.append(item)

        total_analyzed = len(events)
        if total_analyzed == 0:
            exec_summary = "Global monitoring active. No high-severity anomalies detected in current surveillance window."
        else:
            top_evt = events[0]
            exec_summary = (
                f"Global intelligence sweep analyzed {total_analyzed} active events. "
                f"Primary focus centers on '{top_evt.canonical_title}' (Impact {top_evt.importance_score:.1f}/10) "
                f"with {len(breaking_alerts)} high-velocity developing situations tracked across continents."
            )

        return IntelligenceBriefingResponse(
            generated_at=now,
            executive_summary=exec_summary,
            total_events_analyzed=total_analyzed,
            breaking_alerts=breaking_alerts,
            critical_geopolitical=geopolitical,
            humanitarian_hazards=hazards,
            economic_disruptions=economic
        )

    @classmethod
    async def get_event_timeline(
        cls,
        session: AsyncSession,
        event_id: str
    ) -> EventTimelineResponse:
        """
        Builds a chronological evolution timeline of an event across all linked articles.
        """
        stmt = (
            select(Event)
            .options(
                selectinload(Event.article_associations)
                .selectinload(EventArticle.article)
                .selectinload(Article.source)
            )
            .where(Event.id == event_id)
        )
        res = await session.execute(stmt)
        event = res.scalar_one_or_none()

        if not event:
            raise ValueError(f"Event with ID '{event_id}' not found.")

        # Sort associations chronologically by article publication date
        sorted_assocs = sorted(
            event.article_associations,
            key=lambda a: (a.article.published_at or a.created_at) if a.article else a.created_at
        )

        timeline_entries: List[TimelineEntry] = []
        for assoc in sorted_assocs:
            art = assoc.article
            if not art:
                continue

            domain = "wire.report"
            source_name = art.source_id or "Wire Service"
            if art.source:
                domain = art.source.domain
                source_name = art.source.name

            excerpt = art.cleaned_content[:180] + "..." if art.cleaned_content else art.title

            timeline_entries.append(
                TimelineEntry(
                    article_id=art.id,
                    title=art.title,
                    source_name=source_name,
                    source_domain=domain,
                    url=art.url,
                    canonical_url=art.canonical_url,
                    published_at=art.published_at,
                    relationship_type=assoc.relationship_type or "corroborating",
                    similarity_score=assoc.similarity_score or 1.0,
                    excerpt=excerpt
                )
            )

        return EventTimelineResponse(
            event_id=event.id,
            canonical_title=event.canonical_title,
            first_seen_at=event.first_seen_at,
            last_updated_at=event.last_updated_at,
            total_articles=len(timeline_entries),
            timeline=timeline_entries
        )
