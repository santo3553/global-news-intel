import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models import Source, Article
from workers.extraction.extraction_worker import ExtractionWorker


@pytest.mark.asyncio
async def test_extraction_worker_pipeline(async_db: AsyncSession):
    # 1. Setup Source and Pending Article
    source = Source(
        id="src-extract-test",
        name="Kyushu Daily",
        domain="kyushudaily.jp",
        feed_url="https://kyushudaily.jp/rss"
    )
    async_db.add(source)

    article = Article(
        id="art-pending-01",
        source_id="src-extract-test",
        title="M7.1 offshore earthquake triggers alerts in Miyazaki, Japan",
        url="https://kyushudaily.jp/news/m71-earthquake",
        published_at=datetime.now(timezone.utc),
        raw_content="Coastal sirens activated in Miyazaki after M7.1 earthquake struck off the coast of Kyushu.",
        cleaned_content="Coastal sirens activated in Miyazaki after M7.1 earthquake struck off the coast of Kyushu.",
        processing_status="pending"
    )
    async_db.add(article)
    await async_db.commit()

    # 2. Run ExtractionWorker
    worker = ExtractionWorker()
    res = await worker.process_article(async_db, article)

    # 3. Verify extraction result
    assert res["status"] == "extracted"
    assert res["category"] == "natural_disaster"
    assert res["location"]["city"] == "Miyazaki"
    assert res["embedding_dims"] == 384

    # 4. Verify DB update
    updated_art = (await async_db.execute(select(Article).where(Article.id == "art-pending-01"))).scalar_one_or_none()
    assert updated_art is not None
    assert updated_art.processing_status == "extracted"
    assert updated_art.embedding is not None
    assert len(updated_art.embedding) == 384


@pytest.mark.asyncio
async def test_adhoc_extract_api(client: AsyncClient):
    payload = {
        "title": "Clean Energy Treaty Signed at Geneva Summit",
        "content": "Delegates in Geneva, Switzerland successfully ratified a binding carbon reduction treaty."
    }
    response = await client.post("/api/extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "politics"
    assert data["location"]["city"] == "Geneva"
    assert data["location"]["country"] == "Switzerland"
    assert data["location"]["precision"] == "city"
    assert data["location"]["location_confidence"] >= 0.95
    assert len(data["claims"]) >= 1
