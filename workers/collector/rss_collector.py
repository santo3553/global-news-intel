import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.config import settings
from apps.api.app.models import Source, Article
from workers.normalization.normalizer import (
    normalize_url,
    clean_text,
    parse_datetime,
    compute_hashes
)
from workers.normalization.deduplicator import Deduplicator

logger = logging.getLogger("gni.collector")


class RawFeedItem:
    def __init__(
        self,
        title: str,
        link: str,
        summary: str,
        published_at: Optional[str] = None,
        author: Optional[str] = None,
        raw_content: Optional[str] = None
    ):
        self.title = title
        self.link = link
        self.summary = summary
        self.published_at = published_at
        self.author = author
        self.raw_content = raw_content or summary


def parse_feed_xml(xml_content: str) -> List[RawFeedItem]:
    """
    Parses RSS 2.0 or Atom XML content into a standardized list of RawFeedItems.
    Handles varying XML namespaces, tag casing, and alternative date formats.
    """
    items: List[RawFeedItem] = []
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        logger.warning("XML parsing failed: %s", e)
        return items

    # Helper to strip namespace from tag name
    def clean_tag(tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1].lower()
        return tag.lower()

    root_tag = clean_tag(root.tag)

    # 1. Standard RSS 2.0 (<rss><channel><item>...)
    if root_tag in ("rss", "rdf"):
        channel = None
        for child in root:
            if clean_tag(child.tag) == "channel":
                channel = child
                break
        
        target_nodes = channel if channel is not None else root
        for item_node in target_nodes:
            if clean_tag(item_node.tag) != "item":
                continue

            title = ""
            link = ""
            desc = ""
            pub_date = None
            author = None
            content_encoded = None

            for elem in item_node:
                tag = clean_tag(elem.tag)
                text = (elem.text or "").strip()
                if tag == "title":
                    title = text
                elif tag == "link":
                    link = text or elem.attrib.get("href", "")
                elif tag in ("description", "summary"):
                    desc = text
                elif tag in ("pubdate", "date"):
                    pub_date = text
                elif tag in ("creator", "author"):
                    author = text
                elif tag in ("encoded", "content"):
                    content_encoded = text

            if title and (link or desc):
                items.append(
                    RawFeedItem(
                        title=title,
                        link=link,
                        summary=desc,
                        published_at=pub_date,
                        author=author,
                        raw_content=content_encoded or desc
                    )
                )

    # 2. Atom format (<feed><entry>...)
    elif root_tag == "feed":
        for entry in root:
            if clean_tag(entry.tag) != "entry":
                continue

            title = ""
            link = ""
            summary = ""
            content = ""
            pub_date = None
            author = None

            for elem in entry:
                tag = clean_tag(elem.tag)
                text = (elem.text or "").strip()
                if tag == "title":
                    title = text
                elif tag == "link":
                    # In Atom, link is often in href attribute
                    link = elem.attrib.get("href", "") or text
                elif tag == "summary":
                    summary = text
                elif tag == "content":
                    content = text
                elif tag in ("published", "updated"):
                    pub_date = text
                elif tag == "author":
                    for sub in elem:
                        if clean_tag(sub.tag) == "name":
                            author = (sub.text or "").strip()

            if title and (link or summary or content):
                items.append(
                    RawFeedItem(
                        title=title,
                        link=link,
                        summary=summary or content,
                        published_at=pub_date,
                        author=author,
                        raw_content=content or summary
                    )
                )

    return items


class RSSCollector:
    """
    Robust asynchronous collector for fetching and ingesting public news feeds.
    Respects rate limits, timeouts, and performs 3-level deduplication.
    """

    def __init__(self, deduplicator: Optional[Deduplicator] = None):
        self.deduplicator = deduplicator or Deduplicator(
            near_duplicate_threshold=settings.DEDUPLICATION_HASH_THRESHOLD,
            time_window_hours=settings.MAX_CLUSTER_TIME_WINDOW_HOURS
        )
        self.headers = {
            "User-Agent": "GlobalNewsIntelligence/0.1 (+https://github.com/local-first/gni; public news event research)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
        }

    async def fetch_feed(self, feed_url: str, timeout: float = 12.0) -> Optional[str]:
        """Fetches feed XML with timeout and error resilience."""
        try:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
                response = await client.get(feed_url, timeout=timeout)
                if response.status_code == 200:
                    return response.text
                logger.warning("Feed fetch failed [%s] HTTP %s", feed_url, response.status_code)
                return None
        except Exception as e:
            logger.warning("Feed fetch network error [%s]: %s", feed_url, e)
            return None

    async def process_source(
        self,
        session: AsyncSession,
        source: Source,
        max_articles: int = 25
    ) -> Dict[str, Any]:
        """
        Fetches, normalizes, deduplicates, and saves articles from a single source.
        """
        stats = {
            "source_id": source.id,
            "source_name": source.name,
            "fetched": 0,
            "inserted": 0,
            "deduplicated": 0,
            "errors": 0
        }

        xml_data = await self.fetch_feed(source.feed_url)
        if not xml_data:
            stats["errors"] += 1
            return stats

        raw_items = parse_feed_xml(xml_data)
        stats["fetched"] = len(raw_items)

        for raw_item in raw_items[:max_articles]:
            try:
                # 1. Normalization
                canonical_url = normalize_url(raw_item.link)
                clean_t = clean_text(raw_item.title)
                clean_c = clean_text(raw_item.raw_content, max_length=settings.MAX_ARTICLE_LENGTH)
                pub_dt = parse_datetime(raw_item.published_at)
                title_hash, content_hash = compute_hashes(clean_t, clean_c)

                # 2. Deduplication Check
                dup_result = await self.deduplicator.check_duplicate(
                    session=session,
                    url=raw_item.link,
                    canonical_url=canonical_url,
                    title_hash=title_hash,
                    content_hash=content_hash,
                    title=clean_t,
                    cleaned_content=clean_c,
                    published_at=pub_dt
                )

                if dup_result.is_duplicate:
                    stats["deduplicated"] += 1
                    logger.debug(
                        "Deduplicated article [%s]: %s (matches %s)",
                        clean_t[:40], dup_result.duplicate_type, dup_result.matched_article_id
                    )
                    continue

                # 3. Create & Insert Article
                article = Article(
                    source_id=source.id,
                    title=clean_t,
                    url=raw_item.link,
                    canonical_url=canonical_url,
                    author=raw_item.author,
                    published_at=pub_dt,
                    fetched_at=datetime.now(timezone.utc),
                    language=source.language or "en",
                    raw_content=raw_item.raw_content,
                    cleaned_content=clean_c,
                    content_hash=content_hash,
                    title_hash=title_hash,
                    processing_status="pending"
                )
                session.add(article)
                await session.flush()
                stats["inserted"] += 1

            except Exception as e:
                stats["errors"] += 1
                logger.error("Error processing feed item [%s]: %s", raw_item.title, e)

        await session.commit()
        return stats

    async def collect_all_active(
        self,
        session: AsyncSession,
        concurrency_limit: int = 5,
        max_articles_per_feed: int = 25
    ) -> Dict[str, Any]:
        """
        Runs full collection cycle over all active registered sources using bounded concurrency.
        """
        stmt = select(Source).where(Source.active.is_(True))
        result = await session.execute(stmt)
        sources = result.scalars().all()

        total_stats = {
            "sources_total": len(sources),
            "sources_processed": 0,
            "articles_fetched": 0,
            "articles_inserted": 0,
            "articles_deduplicated": 0,
            "errors": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        semaphore = asyncio.Semaphore(concurrency_limit)

        async def worker(source: Source):
            async with semaphore:
                try:
                    res = await self.process_source(session, source, max_articles=max_articles_per_feed)
                    return res
                except Exception as e:
                    logger.error("Source collection worker failed [%s]: %s", source.name, e)
                    return {"errors": 1, "fetched": 0, "inserted": 0, "deduplicated": 0}

        results = await asyncio.gather(*(worker(s) for s in sources), return_exceptions=True)

        for res in results:
            if isinstance(res, dict):
                total_stats["sources_processed"] += 1
                total_stats["articles_fetched"] += res.get("fetched", 0)
                total_stats["articles_inserted"] += res.get("inserted", 0)
                total_stats["articles_deduplicated"] += res.get("deduplicated", 0)
                total_stats["errors"] += res.get("errors", 0)

        logger.info(
            "Collection cycle completed: %d sources, %d fetched, %d inserted, %d deduplicated",
            total_stats["sources_processed"],
            total_stats["articles_fetched"],
            total_stats["articles_inserted"],
            total_stats["articles_deduplicated"]
        )
        return total_stats
