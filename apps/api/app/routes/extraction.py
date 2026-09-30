from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import get_db
from apps.api.app.models import Article
from ai.providers.factory import get_ai_provider
from workers.extraction.geocoder import Geocoder
from workers.extraction.extraction_worker import ExtractionWorker

router = APIRouter(prefix="/api/extract", tags=["AI Extraction"])


class AdHocExtractionRequest(BaseModel):
    title: str = Field(..., min_length=5, description="Article or story headline")
    content: str = Field(..., min_length=10, description="Article body or summary text")


@router.post("", summary="Extract structured event intelligence and geocoding from text")
async def extract_adhoc(payload: AdHocExtractionRequest):
    """
    Direct ad-hoc extraction endpoint:
    Uses AI provider for structured extraction, validates coordinates with Geocoder,
    and returns validated event data.
    """
    provider = get_ai_provider()
    geocoder = Geocoder()

    extracted = await provider.extract_event(payload.title, payload.content)
    resolved_loc = geocoder.resolve(
        raw_name=extracted.location.name,
        country_hint=extracted.location.country,
        text_context=payload.content[:1000],
        llm_lat=extracted.location.latitude,
        llm_lng=extracted.location.longitude
    )

    return {
        "event_title": extracted.event_title,
        "category": extracted.category,
        "subcategory": extracted.subcategory,
        "location": resolved_loc.to_dict(),
        "entities": [e.model_dump() for e in extracted.entities],
        "claims": extracted.claims,
        "severity": extracted.severity,
        "novelty": extracted.novelty,
        "confidence": extracted.confidence,
        "human_impact_estimate": extracted.human_impact_estimate,
        "global_impact_estimate": extracted.global_impact_estimate
    }


@router.post("/article/{article_id}", summary="Trigger extraction pipeline on a stored article")
async def extract_article_by_id(article_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches article from database, runs extraction, computes embeddings, and updates status to 'extracted'.
    """
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article '{article_id}' not found"
        )

    worker = ExtractionWorker()
    return await worker.process_article(db, article)


@router.post("/batch", summary="Run extraction on all pending articles in the database")
async def extract_pending_batch(
    limit: int = Query(25, ge=1, le=100, description="Max articles to extract"),
    db: AsyncSession = Depends(get_db)
):
    worker = ExtractionWorker()
    return await worker.process_pending_batch(db, limit=limit)
