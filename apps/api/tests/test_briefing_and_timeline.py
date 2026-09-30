import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.main import app
from apps.api.app.models import Event, Article, EventArticle, Source


@pytest.mark.asyncio
async def test_executive_briefing_and_sections(async_db: AsyncSession, client: AsyncClient):
    now = datetime.now(timezone.utc)

    # 1. High-velocity hazard event
    evt_hazard = Event(
        id="evt-brief-hazard",
        canonical_title="Typhoon Shanshan Approaching Southern Japan",
        summary="Severe tropical storm bearing down on Kyushu with gale warnings.",
        category="natural_disaster",
        subcategory="typhoon",
        latitude=31.5,
        longitude=130.5,
        country="Japan",
        city="Kagoshima",
        importance_score=8.7,
        confidence_score=0.92,
        human_impact_score=8.5,
        global_impact_score=6.5,
        development_velocity_score=8.0,
        source_coverage_score=6.0,
        first_seen_at=now - timedelta(hours=3),
        last_updated_at=now,
        status="active"
    )

    # 2. Geopolitical event
    evt_geo = Event(
        id="evt-brief-geo",
        canonical_title="Multilateral Arctic Navigation and Resource Treaty",
        summary="Northern states conclude landmark sovereign navigation protocol in Oslo.",
        category="politics",
        subcategory="treaty",
        latitude=59.9,
        longitude=10.7,
        country="Norway",
        city="Oslo",
        importance_score=7.8,
        confidence_score=0.88,
        human_impact_score=3.0,
        global_impact_score=8.5,
        development_velocity_score=4.0,
        source_coverage_score=5.0,
        first_seen_at=now - timedelta(hours=6),
        last_updated_at=now - timedelta(hours=1),
        status="active"
    )

    # 3. Economic event
    evt_econ = Event(
        id="evt-brief-econ",
        canonical_title="Global Semiconductor Supply Realignment",
        summary="Chip manufacturers announce joint silicon foundry in Dresden.",
        category="economy",
        subcategory="semiconductors",
        latitude=51.0,
        longitude=13.7,
        country="Germany",
        city="Dresden",
        importance_score=7.4,
        confidence_score=0.86,
        human_impact_score=2.0,
        global_impact_score=7.0,
        economic_impact_score=8.2,
        development_velocity_score=5.0,
        source_coverage_score=4.0,
        first_seen_at=now - timedelta(hours=12),
        last_updated_at=now - timedelta(hours=2),
        status="active"
    )

    async_db.add_all([evt_hazard, evt_geo, evt_econ])
    await async_db.commit()

    res = await client.get("/api/briefing")
    assert res.status_code == 200
    data = res.json()

    assert data["total_events_analyzed"] >= 3
    assert len(data["executive_summary"]) > 20
    # Breaking alerts should capture high-velocity typhoon
    assert any(b["event_id"] == "evt-brief-hazard" for b in data["breaking_alerts"])
    # Geopolitical section should capture arctic treaty
    assert any(b["event_id"] == "evt-brief-geo" for b in data["critical_geopolitical"])
    # Hazards section should capture typhoon
    assert any(b["event_id"] == "evt-brief-hazard" for b in data["humanitarian_hazards"])
    # Economic section should capture semiconductor foundry
    assert any(b["event_id"] == "evt-brief-econ" for b in data["economic_disruptions"])


@pytest.mark.asyncio
async def test_event_timeline_chronology(async_db: AsyncSession, client: AsyncClient):
    now = datetime.now(timezone.utc)

    # Setup Event
    evt = Event(
        id="evt-timeline-test",
        canonical_title="Geneva Global Clean Energy Accord",
        summary="Nations agree on accelerated clean energy pact.",
        category="politics",
        latitude=46.2,
        longitude=6.1,
        country="Switzerland",
        city="Geneva",
        importance_score=8.0,
        confidence_score=0.90,
        first_seen_at=now - timedelta(hours=5),
        last_updated_at=now,
        status="active"
    )
    async_db.add(evt)

    # Setup 2 Articles published sequentially
    art1 = Article(
        id="art-time-01",
        source_id="reuters.com",
        title="Draft clean energy text circulated at Geneva talks",
        url="https://wire.com/draft",
        published_at=now - timedelta(hours=4),
        cleaned_content="Negotiators present preliminary draft text.",
        processing_status="clustered"
    )
    art2 = Article(
        id="art-time-02",
        source_id="apnews.com",
        title="Geneva energy accord unanimously finalized",
        url="https://wire.com/final",
        published_at=now - timedelta(hours=1),
        cleaned_content="Delegates celebrate final signature on renewable pact.",
        processing_status="clustered"
    )
    async_db.add_all([art1, art2])
    await async_db.flush()

    link1 = EventArticle(
        event_id=evt.id,
        article_id=art1.id,
        relationship_type="primary",
        similarity_score=1.0,
        created_at=now - timedelta(hours=4)
    )
    link2 = EventArticle(
        event_id=evt.id,
        article_id=art2.id,
        relationship_type="update",
        similarity_score=0.88,
        created_at=now - timedelta(hours=1)
    )
    async_db.add_all([link1, link2])
    await async_db.commit()

    res = await client.get(f"/api/events/{evt.id}/timeline")
    assert res.status_code == 200
    timeline_data = res.json()

    assert timeline_data["event_id"] == evt.id
    assert timeline_data["total_articles"] == 2
    entries = timeline_data["timeline"]
    assert len(entries) == 2
    # Verify chronological order (art1 first, art2 second)
    assert entries[0]["article_id"] == "art-time-01"
    assert entries[1]["article_id"] == "art-time-02"
    assert entries[0]["relationship_type"] == "primary"
    assert entries[1]["relationship_type"] == "update"


@pytest.mark.asyncio
async def test_events_search_endpoint(async_db: AsyncSession, client: AsyncClient):
    now = datetime.now(timezone.utc)

    evt = Event(
        id="evt-search-test",
        canonical_title="Reykjanes Volcanic Eruption",
        summary="Fissure eruption opens near Grindavik with lava flows threatening local road networks.",
        category="natural_disaster",
        subcategory="volcano",
        latitude=63.8,
        longitude=-22.4,
        country="Iceland",
        city="Grindavik",
        importance_score=7.9,
        confidence_score=0.94,
        first_seen_at=now,
        last_updated_at=now,
        status="active"
    )
    async_db.add(evt)
    await async_db.commit()

    # Search by title keyword
    res_title = await client.get("/api/events/search?q=Reykjanes")
    assert res_title.status_code == 200
    results_title = res_title.json()
    assert any(e["id"] == "evt-search-test" for e in results_title)

    # Search by country
    res_country = await client.get("/api/events/search?q=Iceland")
    assert res_country.status_code == 200
    results_country = res_country.json()
    assert any(e["id"] == "evt-search-test" for e in results_country)

    # Search by summary keyword
    res_summary = await client.get("/api/events/search?q=Grindavik")
    assert res_summary.status_code == 200
    results_summary = res_summary.json()
    assert any(e["id"] == "evt-search-test" for e in results_summary)

