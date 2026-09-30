import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.models import Event, Article, EventArticle, Source


@pytest.mark.asyncio
async def test_events_api_endpoints(client: AsyncClient, async_db: AsyncSession):
    now = datetime.now(timezone.utc)

    # 1. Setup Source, Event, and Article in Tokyo, Japan
    src = Source(id="src-api-test", name="Tokyo Times", domain="tokyotimes.com", feed_url="https://tokyotimes.com/rss")
    async_db.add(src)

    evt_japan = Event(
        id="evt-test-japan",
        canonical_title="Tokyo Metro Transit Modernization Plan",
        summary="Tokyo unveils automated magnetic transit corridors.",
        category="economy",
        latitude=35.68,
        longitude=139.76,
        country="Japan",
        city="Tokyo",
        importance_score=8.5,
        confidence_score=0.92,
        first_seen_at=now,
        last_updated_at=now,
        status="active"
    )
    async_db.add(evt_japan)

    art_japan = Article(
        id="art-test-japan-01",
        source_id="src-api-test",
        title="Tokyo unveils automated magnetic transit corridors",
        url="https://tokyotimes.com/transit",
        published_at=now,
        processing_status="clustered"
    )
    async_db.add(art_japan)

    link = EventArticle(
        event_id="evt-test-japan",
        article_id="art-test-japan-01",
        similarity_score=0.95,
        relationship_type="primary",
        created_at=now
    )
    async_db.add(link)

    # 2. Setup Event in Paris, France
    evt_france = Event(
        id="evt-test-france",
        canonical_title="Paris International Aerospace Exhibition",
        summary="New hydrogen passenger aircraft demonstrated in Paris.",
        category="science",
        latitude=48.85,
        longitude=2.35,
        country="France",
        city="Paris",
        importance_score=7.0,
        confidence_score=0.88,
        first_seen_at=now,
        last_updated_at=now,
        status="active"
    )
    async_db.add(evt_france)
    await async_db.commit()

    # 3. Test GET /api/events with bounding box for East Asia (enclosing Japan)
    # Bbox: minLng=120, minLat=20, maxLng=150, maxLat=50
    bbox_asia = "120,20,150,50"
    res_bbox = await client.get(f"/api/events?bbox={bbox_asia}")
    assert res_bbox.status_code == 200
    events_asia = res_bbox.json()
    assert len(events_asia) == 1
    assert events_asia[0]["id"] == "evt-test-japan"

    # 4. Test GET /api/events/{id} with article associations
    res_detail = await client.get("/api/events/evt-test-japan")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["canonical_title"] == "Tokyo Metro Transit Modernization Plan"
    assert detail["article_count"] == 1
    assert len(detail["articles"]) == 1
    assert detail["articles"][0]["id"] == "art-test-japan-01"

    # 5. Test GET /api/events/top
    res_top = await client.get("/api/events/top?limit=2")
    assert res_top.status_code == 200
    top_events = res_top.json()
    assert len(top_events) == 2
    assert top_events[0]["importance_score"] >= top_events[1]["importance_score"]

    # 6. Test GET /api/events/nearby (near Yokohama, 30km from Tokyo)
    # Yokohama lat=35.44, lng=139.63
    res_nearby = await client.get("/api/events/nearby?lat=35.44&lng=139.63&radius_km=100")
    assert res_nearby.status_code == 200
    nearby = res_nearby.json()
    assert len(nearby) == 1
    assert nearby[0]["id"] == "evt-test-japan"
    assert "distance_km" in nearby[0]
    assert nearby[0]["distance_km"] < 50.0
