import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.models import Source, Article


@pytest.mark.asyncio
async def test_seed_and_list_sources(client: AsyncClient):
    # 1. Seed sources
    seed_resp = await client.post("/api/sources/seed")
    assert seed_resp.status_code == 200
    data = seed_resp.json()
    assert data["status"] == "success"
    assert data["sources_seeded"] > 0

    # 2. List sources
    list_resp = await client.get("/api/sources")
    assert list_resp.status_code == 200
    sources = list_resp.json()
    assert len(sources) > 15
    first = sources[0]
    assert "name" in first
    assert "feed_url" in first
    assert "reliability_score" in first


@pytest.mark.asyncio
async def test_create_and_get_source(client: AsyncClient):
    new_src = {
        "name": "Local Independent News",
        "domain": "localindependent.org",
        "feed_url": "https://localindependent.org/rss.xml",
        "source_type": "rss",
        "country": "US",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    }
    create_resp = await client.post("/api/sources", json=new_src)
    assert create_resp.status_code == 201
    created_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/sources/{created_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Local Independent News"


@pytest.mark.asyncio
async def test_list_and_get_articles(client: AsyncClient, async_db: AsyncSession):
    # Insert test source & article directly
    source = Source(
        id="src-test-api",
        name="API Test Wire",
        domain="apitest.org",
        feed_url="https://apitest.org/rss"
    )
    async_db.add(source)

    now = datetime.now(timezone.utc)
    article = Article(
        id="art-test-api-01",
        source_id="src-test-api",
        title="Test Article Title for API",
        url="https://apitest.org/news/test-1",
        published_at=now,
        raw_content="Content for API test.",
        cleaned_content="Content for API test.",
        processing_status="pending"
    )
    async_db.add(article)
    await async_db.commit()

    # Query articles list
    list_resp = await client.get("/api/articles")
    assert list_resp.status_code == 200
    articles = list_resp.json()
    assert len(articles) >= 1
    assert any(a["id"] == "art-test-api-01" for a in articles)

    # Query single article detail
    detail_resp = await client.get("/api/articles/art-test-api-01")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["title"] == "Test Article Title for API"
