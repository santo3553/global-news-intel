import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models import Source, Article
from workers.normalization.normalizer import compute_hashes
from workers.normalization.deduplicator import (
    tokenize,
    get_shingles,
    jaccard_similarity,
    compute_text_similarity,
    Deduplicator
)


def test_token_and_shingle_similarity():
    text1 = "A magnitude 7.1 earthquake struck southern Japan on Monday."
    text2 = "A magnitude 7.1 earthquake struck southern Japan on Monday morning."
    text3 = "Unrelated news story about football championship finals in Europe."

    sim_high = compute_text_similarity(text1, text2)
    sim_low = compute_text_similarity(text1, text3)

    assert sim_high > 0.70
    assert sim_low < 0.20


@pytest.mark.asyncio
async def test_deduplicator_exact_url(async_db: AsyncSession):
    # Setup source and existing article
    source = Source(id="src-1", name="Test News", domain="test.com", feed_url="https://test.com/rss")
    async_db.add(source)

    now = datetime.now(timezone.utc)
    t_hash, c_hash = compute_hashes("Existing Title", "Existing Content")
    article = Article(
        id="art-existing",
        source_id="src-1",
        title="Existing Title",
        url="https://test.com/news/123",
        canonical_url="https://test.com/news/123",
        published_at=now,
        title_hash=t_hash,
        content_hash=c_hash,
        cleaned_content="Existing Content"
    )
    async_db.add(article)
    await async_db.commit()

    dedup = Deduplicator()

    # Test Level 1: Exact URL match
    res = await dedup.check_duplicate(
        session=async_db,
        url="https://test.com/news/123",
        canonical_url="https://test.com/news/123",
        title_hash="different_hash",
        content_hash="different_content_hash",
        title="Different Title",
        cleaned_content="Different Content",
        published_at=now
    )
    assert res.is_duplicate is True
    assert res.duplicate_type == "exact_url"
    assert res.matched_article_id == "art-existing"


@pytest.mark.asyncio
async def test_deduplicator_exact_hash(async_db: AsyncSession):
    source = Source(id="src-2", name="Wire Service", domain="wire.com", feed_url="https://wire.com/rss")
    async_db.add(source)

    now = datetime.now(timezone.utc)
    t_hash, c_hash = compute_hashes("Breaking Story", "Identical article content text.")
    article = Article(
        id="art-wire-01",
        source_id="src-2",
        title="Breaking Story",
        url="https://wire.com/story-a",
        canonical_url="https://wire.com/story-a",
        published_at=now,
        title_hash=t_hash,
        content_hash=c_hash,
        cleaned_content="Identical article content text."
    )
    async_db.add(article)
    await async_db.commit()

    dedup = Deduplicator()

    # Test Level 2: Content Hash collision on different URL
    res = await dedup.check_duplicate(
        session=async_db,
        url="https://repost.com/another-url",
        canonical_url="https://repost.com/another-url",
        title_hash="unique_title_hash",
        content_hash=c_hash,
        title="Unique Title",
        cleaned_content="Identical article content text.",
        published_at=now
    )
    assert res.is_duplicate is True
    assert res.duplicate_type == "exact_content"
    assert res.matched_article_id == "art-wire-01"


@pytest.mark.asyncio
async def test_deduplicator_syndicated_near_duplicate(async_db: AsyncSession):
    source = Source(id="src-3", name="National News", domain="nat.com", feed_url="https://nat.com/rss")
    async_db.add(source)

    now = datetime.now(timezone.utc)
    original_text = (
        "Geneva Climate Summit: Nations agreed to a legally binding mandate to accelerate "
        "the global clean energy transition schedule by 2035 with a dedicated adaptation fund."
    )
    t_hash, c_hash = compute_hashes("Historic Clean Energy Agreement Reached at Geneva Summit", original_text)

    article = Article(
        id="art-synd-orig",
        source_id="src-3",
        title="Historic Clean Energy Agreement Reached at Geneva Summit",
        url="https://nat.com/orig",
        canonical_url="https://nat.com/orig",
        published_at=now,
        title_hash=t_hash,
        content_hash=c_hash,
        cleaned_content=original_text
    )
    async_db.add(article)
    await async_db.commit()

    dedup = Deduplicator(near_duplicate_threshold=0.80)

    # Substantially identical text published by an affiliate with rewritten headline
    syndicated_text = (
        "Geneva Climate Summit: Nations agreed to a legally binding mandate to accelerate "
        "the global clean energy transition schedule by 2035 with a dedicated adaptation fund announced today."
    )
    synd_title = "Global Leaders Agree on Accelerated Clean Power Schedule at Geneva Talks"
    s_thash, s_chash = compute_hashes(synd_title, syndicated_text)

    res = await dedup.check_duplicate(
        session=async_db,
        url="https://affiliate.com/syndicated-story",
        canonical_url="https://affiliate.com/syndicated-story",
        title_hash=s_thash,
        content_hash=s_chash,
        title=synd_title,
        cleaned_content=syndicated_text,
        published_at=now
    )
    assert res.is_duplicate is True
    assert res.duplicate_type == "syndicated_near_duplicate"
    assert res.matched_article_id == "art-synd-orig"
