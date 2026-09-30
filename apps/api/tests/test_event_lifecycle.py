import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models import Source, Article, Event, EventArticle
from workers.clustering.clusterer import EventClusterer
from ai.providers.factory import get_ai_provider
from workers.embeddings.embedding_engine import EmbeddingEngine


@pytest.mark.asyncio
async def test_event_clustering_lifecycle_and_merging(async_db: AsyncSession):
    # 1. Setup Source
    source = Source(id="src-lifecycle-test", name="Global Wire", domain="wire.com", feed_url="https://wire.com/rss")
    async_db.add(source)
    await async_db.commit()

    clusterer = EventClusterer(threshold=0.65)
    ai_provider = get_ai_provider()
    embedding_engine = EmbeddingEngine()
    now = datetime.now(timezone.utc)

    # ----------------------------------------------------
    # Article 1: Initial Earthquake Alert
    # ----------------------------------------------------
    art1_content = "A magnitude 7.1 earthquake struck off Miyazaki coast in Kyushu, southern Japan."
    art1 = Article(
        id="art-quake-1",
        source_id="src-lifecycle-test",
        title="Magnitude 7.1 earthquake strikes southern Japan off Miyazaki coast",
        url="https://wire.com/quake-1",
        published_at=now - timedelta(hours=2),
        cleaned_content=art1_content,
        embedding=await embedding_engine.embed_text(art1_content),
        processing_status="extracted"
    )
    async_db.add(art1)
    await async_db.commit()

    ext1 = await ai_provider.extract_event(art1.title, art1_content)
    dec1 = await clusterer.cluster_article(async_db, art1, ext1)

    assert dec1.action == "created"
    event_1_id = dec1.event_id

    # ----------------------------------------------------
    # Article 2: Corroborating Report (Same Event)
    # ----------------------------------------------------
    art2_content = "Japanese meteorological agency reports M7.1 tremor off Miyazaki with tsunami advisories in Kyushu."
    art2 = Article(
        id="art-quake-2",
        source_id="src-lifecycle-test",
        title="Japan issues tsunami advisories after M7.1 quake in Miyazaki, Kyushu",
        url="https://wire.com/quake-2",
        published_at=now - timedelta(hours=1, minutes=30),
        cleaned_content=art2_content,
        embedding=await embedding_engine.embed_text(art2_content),
        processing_status="extracted"
    )
    async_db.add(art2)
    await async_db.commit()

    ext2 = await ai_provider.extract_event(art2.title, art2_content)
    dec2 = await clusterer.cluster_article(async_db, art2, ext2)

    # Must MERGE into event_1_id!
    assert dec2.action == "merged"
    assert dec2.event_id == event_1_id

    # ----------------------------------------------------
    # Article 3: Update on Same Event
    # ----------------------------------------------------
    art3_content = "Authorities in Japan have canceled all tsunami advisories following the Miyazaki M7.1 tremor."
    art3 = Article(
        id="art-quake-3",
        source_id="src-lifecycle-test",
        title="Update: Tsunami warnings canceled after southern Japan earthquake",
        url="https://wire.com/quake-3",
        published_at=now - timedelta(minutes=45),
        cleaned_content=art3_content,
        embedding=await embedding_engine.embed_text(art3_content),
        processing_status="extracted"
    )
    async_db.add(art3)
    await async_db.commit()

    ext3 = await ai_provider.extract_event(art3.title, art3_content)
    dec3 = await clusterer.cluster_article(async_db, art3, ext3)

    assert dec3.action == "merged"
    assert dec3.event_id == event_1_id

    # Verify only ONE Event exists for all 3 articles
    events = (await async_db.execute(select(Event))).scalars().all()
    assert len(events) == 1
    assert events[0].id == event_1_id

    # Verify 3 EventArticle associations exist
    links = (await async_db.execute(select(EventArticle).where(EventArticle.event_id == event_1_id))).scalars().all()
    assert len(links) == 3

    # ----------------------------------------------------
    # Article 4: Completely Unrelated Story (Geneva Climate Pact)
    # ----------------------------------------------------
    art4_content = "142 nations in Geneva, Switzerland signed a binding clean energy transition treaty."
    art4 = Article(
        id="art-geneva-1",
        source_id="src-lifecycle-test",
        title="Geneva Climate Summit: Nations ratify clean energy transition pact",
        url="https://wire.com/geneva-1",
        published_at=now - timedelta(hours=5),
        cleaned_content=art4_content,
        embedding=await embedding_engine.embed_text(art4_content),
        processing_status="extracted"
    )
    async_db.add(art4)
    await async_db.commit()

    ext4 = await ai_provider.extract_event(art4.title, art4_content)
    dec4 = await clusterer.cluster_article(async_db, art4, ext4)

    # Must create a separate NEW event!
    assert dec4.action == "created"
    assert dec4.event_id != event_1_id

    # Now exactly TWO distinct events must exist in DB
    all_events = (await async_db.execute(select(Event))).scalars().all()
    assert len(all_events) == 2
