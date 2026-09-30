import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.main import app
from apps.api.app.models import Event, Article, EventArticle, Source
from workers.ranking.ranking_worker import EventRankingWorker
from workers.clustering.clusterer import EventClusterer
from ai.schemas.extraction import ExtractedEventData, ExtractedLocation, ExtractedEntity
from workers.embeddings.embedding_engine import EmbeddingEngine


@pytest.mark.asyncio
async def test_ranking_worker_end_to_end(async_db: AsyncSession):
    now = datetime.now(timezone.utc)

    # 1. Create a Source
    src = Source(
        id="src-rank-reuters",
        name="Reuters World",
        domain="reuters.com",
        feed_url="https://reuters.com/rss",
        country="GB",
        reliability_score=0.95
    )
    async_db.add(src)

    # 2. Create Event
    evt = Event(
        id="evt-rank-test-01",
        canonical_title="Mediterranean Seismic Incident",
        summary="A shallow undersea earthquake observed south of Crete.",
        category="natural_disaster",
        subcategory="earthquake",
        latitude=35.0,
        longitude=25.0,
        country="Greece",
        city="Heraklion",
        location_confidence=0.95,
        importance_score=5.0,
        confidence_score=0.5,
        human_impact_score=6.0,
        global_impact_score=5.0,
        first_seen_at=now - timedelta(hours=2),
        last_updated_at=now,
        status="active"
    )
    async_db.add(evt)

    # 3. Create Article linked to Source and Event
    art = Article(
        id="art-rank-01",
        source_id="src-rank-reuters",
        title="Crete hit by moderate offshore quake; no damage reported",
        url="https://reuters.com/crete-quake",
        published_at=now,
        cleaned_content="Undersea tremor shakes southern Greek island of Crete.",
        processing_status="clustered"
    )
    async_db.add(art)
    await async_db.flush()

    link = EventArticle(
        event_id=evt.id,
        article_id=art.id,
        similarity_score=0.92,
        relationship_type="primary",
        created_at=now
    )
    async_db.add(link)
    await async_db.commit()

    # 4. Run EventRankingWorker
    rank_res = await EventRankingWorker.update_event_ranking(async_db, evt)
    await async_db.commit()

    assert rank_res["event_id"] == "evt-rank-test-01"
    assert evt.importance_score > 0.0
    assert evt.confidence_score > 0.0
    assert evt.source_coverage_score > 0.0
    assert evt.development_velocity_score > 0.0


@pytest.mark.asyncio
async def test_api_sorting_and_decay_endpoints(async_db: AsyncSession):
    now = datetime.now(timezone.utc)

    # Insert two events with distinct importance and velocity
    evt1 = Event(
        id="evt-sort-high-imp",
        canonical_title="Critical Continental Power Disruption",
        summary="Grid malfunction across Central Europe.",
        category="infrastructure",
        latitude=50.0,
        longitude=10.0,
        country="Germany",
        importance_score=9.2,
        confidence_score=0.75,
        development_velocity_score=3.0,
        first_seen_at=now - timedelta(hours=5),
        last_updated_at=now - timedelta(hours=1),
        status="active"
    )
    evt2 = Event(
        id="evt-sort-high-vel",
        canonical_title="Breaking Tropical Cyclone Landfall",
        summary="Fast-moving category 4 typhoon approaching eastern coastline.",
        category="natural_disaster",
        latitude=15.0,
        longitude=120.0,
        country="Philippines",
        importance_score=8.1,
        confidence_score=0.92,
        development_velocity_score=9.5,
        first_seen_at=now - timedelta(minutes=45),
        last_updated_at=now,
        status="active"
    )
    async_db.add_all([evt1, evt2])
    await async_db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test sort_by=importance
        res_imp = await client.get("/api/events?sort_by=importance&limit=10")
        assert res_imp.status_code == 200
        data_imp = res_imp.json()
        assert len(data_imp) >= 2
        # evt1 (9.2) should precede evt2 (8.1)
        scores = [e["importance_score"] for e in data_imp]
        assert scores[0] >= scores[1]

        # Test sort_by=velocity
        res_vel = await client.get("/api/events?sort_by=velocity&limit=10")
        assert res_vel.status_code == 200
        data_vel = res_vel.json()
        vels = [e["development_velocity_score"] for e in data_vel]
        assert vels[0] >= vels[1]

        # Test POST /api/events/decay
        res_decay = await client.post("/api/events/decay?max_events=10")
        assert res_decay.status_code == 200
        decay_data = res_decay.json()
        assert decay_data["status"] == "completed"
