from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import get_db
from apps.api.app.models import Article
from apps.api.app.schemas.article import ArticleResponse
from workers.collector.rss_collector import RSSCollector

router = APIRouter(prefix="/api/articles", tags=["Articles"])


@router.get("", response_model=List[ArticleResponse], summary="List ingested articles with pagination")
async def list_articles(
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    status: Optional[str] = Query(None, description="Filter by processing status (pending, normalized, extracted, etc.)"),
    limit: int = Query(50, ge=1, le=200, description="Max articles to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Article)
    if source_id:
        stmt = stmt.where(Article.source_id == source_id)
    if status:
        stmt = stmt.where(Article.processing_status == status)

    stmt = stmt.order_by(Article.published_at.desc(), Article.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{article_id}", response_model=ArticleResponse, summary="Get full article details by ID")
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{article_id}' not found"
        )
    return article


@router.post("/ingest", summary="Trigger news collection and deduplication cycle")
async def trigger_ingestion(
    max_per_feed: int = Query(15, ge=1, le=50, description="Max articles to fetch per feed"),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually triggers an ingestion cycle across all active sources.
    Fetches XML, normalizes content, performs 3-level deduplication, and stores new articles.
    """
    collector = RSSCollector()
    stats = await collector.collect_all_active(
        session=db,
        concurrency_limit=5,
        max_articles_per_feed=max_per_feed
    )
    return {
        "status": "completed",
        "details": stats
    }
