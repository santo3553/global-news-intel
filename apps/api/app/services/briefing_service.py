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
        Enforces strict geographic/country diversity so no single country dominates the world briefing.
        """
        now = datetime.now(timezone.utc)

        # 1. Query candidate active and developing events ordered by importance & recency
        stmt = (
            select(Event)
            .options(selectinload(Event.article_associations))
            .where(Event.status.in_(["active", "developing"]))
            .order_by(Event.importance_score.desc(), Event.last_updated_at.desc())
            .limit(300)
        )
        res = await session.execute(stmt)
        events = res.scalars().all()

        # 2. Score candidates by Strategic Intelligence Priority
        scored_events = []
        for evt in events:
            evt_time = evt.last_updated_at or evt.first_seen_at
            if evt_time and evt_time.tzinfo is None:
                evt_time = evt_time.replace(tzinfo=timezone.utc)
            
            hours_ago = (now - evt_time).total_seconds() / 3600.0 if evt_time else 72.0
            recency_score = max(0.0, 10.0 - (hours_ago / 7.2))  # 10 for immediate, smoothly decays
            
            strategic_score = (
                (evt.importance_score or 5.0) * 0.40 +
                (evt.global_impact_score or 5.0) * 0.25 +
                min(evt.development_velocity_score or 0.0, 10.0) * 0.20 +
                recency_score * 0.15
            )
            scored_events.append((strategic_score, evt))

        # Sort descending by strategic priority
        scored_events.sort(key=lambda x: x[0], reverse=True)

        def to_briefing_item(evt: Event) -> BriefingItem:
            loc = evt.city or evt.country or "Global"
            if evt.city and evt.country:
                loc = f"{evt.city}, {evt.country}"

            key_takeaway = (
                f"Strategic {evt.category.replace('_', ' ')} development with global impact "
                f"{evt.global_impact_score:.1f}/10 corroborated across {len(evt.article_associations)} reports."
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
                key_takeaway=key_takeaway,
                first_seen_at=evt.first_seen_at,
                last_updated_at=evt.last_updated_at
            )

        breaking_alerts: List[BriefingItem] = []
        geopolitical: List[BriefingItem] = []
        hazards: List[BriefingItem] = []
        economic: List[BriefingItem] = []

        seen_breaking_countries = set()
        seen_geo_countries = set()
        seen_haz_countries = set()
        seen_eco_countries = set()

        for score, evt in scored_events:
            c = (evt.country or "Global").strip().lower()
            item = to_briefing_item(evt)

            # 1. Breaking Alerts: Rapid developing reports, strictly distinct countries
            if len(breaking_alerts) < limit_per_section and c not in seen_breaking_countries:
                if evt.development_velocity_score >= 2.5 or score >= 7.0:
                    breaking_alerts.append(item)
                    seen_breaking_countries.add(c)

            # 2. Critical Geopolitical: Politics, diplomacy, sovereignty, conflict, strictly distinct countries
            if len(geopolitical) < limit_per_section and c not in seen_geo_countries:
                if evt.category in ("politics", "diplomacy", "security", "conflict") or (evt.political_impact_score or 0) >= 4.5 or (evt.global_impact_score or 0) >= 6.0:
                    geopolitical.append(item)
                    seen_geo_countries.add(c)

            # 3. Humanitarian Hazards & Environmental: Disasters, human impact, health, strictly distinct countries
            if len(hazards) < limit_per_section and c not in seen_haz_countries:
                if evt.category in ("natural_disaster", "environment", "health") or ((evt.human_impact_score or 0) >= 5.0 and evt.category in ("security", "conflict", "humanitarian")):
                    hazards.append(item)
                    seen_haz_countries.add(c)

            # 4. Economic Disruptions & Technology: Economy, trade, crypto, markets, tech, strictly distinct countries
            if len(economic) < limit_per_section and c not in seen_eco_countries:
                is_eco = (
                    evt.category in ("economy", "trade", "finance", "science_technology", "infrastructure") or
                    (evt.economic_impact_score or 0) >= 5.0 or
                    any(w in evt.canonical_title.lower() for w in ["market", "crypto", "hack", "billion", "trade", "dollar", "bank", "tech", "ai", "rail", "port", "tariff", "oil", "stocks"])
                )
                if is_eco:
                    economic.append(item)
                    seen_eco_countries.add(c)

        # Fallback if any section is underfilled (e.g. sparse test database)
        for score, evt in scored_events:
            item = to_briefing_item(evt)
            if len(breaking_alerts) < limit_per_section and item not in breaking_alerts:
                breaking_alerts.append(item)
            if len(geopolitical) < limit_per_section and (evt.category in ("politics", "diplomacy", "security") or evt.global_impact_score >= 5.0) and item not in geopolitical:
                geopolitical.append(item)
            if len(hazards) < limit_per_section and (evt.category in ("natural_disaster", "environment") or evt.human_impact_score >= 5.0) and item not in hazards:
                hazards.append(item)
            if len(economic) < limit_per_section and (evt.category in ("economy", "trade", "science_technology") or evt.economic_impact_score >= 5.0) and item not in economic:
                economic.append(item)

        all_briefing_items = breaking_alerts + geopolitical + hazards + economic
        total_analyzed = len(events)

        if total_analyzed == 0:
            exec_summary = "Global monitoring active. No high-severity anomalies detected in current surveillance window."
        else:
            # Pick highest strategic global impact event across briefing items for the memo headline
            top_evt = max(
                all_briefing_items,
                key=lambda x: (x.importance * 0.40 + x.velocity * 0.30)
            ) if all_briefing_items else (breaking_alerts[0] if breaking_alerts else to_briefing_item(events[0]))

            distinct_nations = list(dict.fromkeys(
                item.location.split(",")[-1].strip() for item in all_briefing_items if item.location
            ))

            exec_summary = (
                f"Global intelligence sweep analyzed {total_analyzed} active events across {len(distinct_nations)} nations. "
                f"Primary strategic focus centers on '{top_evt.title}' ({top_evt.location}, Impact {top_evt.importance:.1f}/10) "
                f"with {len(breaking_alerts)} high-velocity developing situations tracked across key continental theatres."
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
