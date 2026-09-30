import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models import Source, Article, Event, EventArticle, Entity, EventEntity


@pytest.mark.asyncio
async def test_create_and_query_models(async_db: AsyncSession):
    # 1. Create a Source
    source = Source(
        id="src-reuters-01",
        name="Reuters",
        domain="reuters.com",
        feed_url="https://www.reutersagency.com/feed/?best-topics=world&post_type=best",
        source_type="rss",
        country="GB",
        language="en",
        reliability_score=0.95
    )
    async_db.add(source)
    await async_db.commit()

    # Query source
    res = await async_db.execute(select(Source).where(Source.id == "src-reuters-01"))
    fetched_source = res.scalar_one_or_none()
    assert fetched_source is not None
    assert fetched_source.name == "Reuters"
    assert fetched_source.reliability_score == 0.95

    # 2. Create an Article
    now = datetime.now(timezone.utc)
    article = Article(
        id="art-001",
        source_id="src-reuters-01",
        title="Major earthquake strikes southern Japan",
        url="https://reuters.com/world/asia-pacific/japan-quake-2026",
        published_at=now,
        raw_content="A magnitude 6.8 earthquake struck Kyushu in southern Japan...",
        cleaned_content="A magnitude 6.8 earthquake struck Kyushu in southern Japan...",
        content_hash="abc123hash",
        title_hash="def456hash",
        processing_status="extracted"
    )
    async_db.add(article)
    await async_db.commit()

    # 3. Create an Event
    event = Event(
        id="evt-001",
        canonical_title="Southern Japan M6.8 Earthquake",
        summary="A major magnitude 6.8 earthquake struck southern Japan with initial tsunami advisories issued.",
        category="natural_disaster",
        subcategory="earthquake",
        latitude=32.8,
        longitude=131.4,
        country="Japan",
        admin_region="Kyushu",
        city="Kumamoto",
        importance_score=8.5,
        confidence_score=0.92,
        human_impact_score=8.0,
        global_impact_score=7.0,
        status="active"
    )
    async_db.add(event)
    await async_db.commit()

    # 4. Link Event to Article
    event_article = EventArticle(
        event_id="evt-001",
        article_id="art-001",
        similarity_score=0.98,
        relationship_type="primary"
    )
    async_db.add(event_article)
    await async_db.commit()

    # 5. Verify Event Query with Article link
    res_event = await async_db.execute(select(Event).where(Event.id == "evt-001"))
    fetched_event = res_event.scalar_one_or_none()
    assert fetched_event is not None
    assert fetched_event.latitude == 32.8
    assert fetched_event.longitude == 131.4
    assert fetched_event.importance_score == 8.5
