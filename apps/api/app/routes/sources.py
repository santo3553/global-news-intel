from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import get_db
from apps.api.app.models import Source
from apps.api.app.schemas.source import SourceResponse, SourceCreate
from workers.collector.sources_catalog import CURATED_SOURCES

router = APIRouter(prefix="/api/sources", tags=["Sources"])


@router.get("", response_model=List[SourceResponse], summary="List all news sources")
async def list_sources(
    active_only: bool = Query(default=True, description="Filter for active feeds only"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Source)
    if active_only:
        stmt = stmt.where(Source.active.is_(True))
    stmt = stmt.order_by(Source.reliability_score.desc(), Source.name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{source_id}", response_model=SourceResponse, summary="Get source details by ID")
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Source).where(Source.id == source_id)
    result = await db.execute(stmt)
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source '{source_id}' not found")
    return source


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED, summary="Create a new news source")
async def create_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    # Check if feed_url already registered
    existing_stmt = select(Source).where(Source.feed_url == payload.feed_url)
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source with feed URL '{payload.feed_url}' already exists ({existing.id})"
        )

    source = Source(**payload.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.post("/seed", summary="Seed or update the default curated global sources catalog")
async def seed_sources(db: AsyncSession = Depends(get_db)):
    """
    Populates or refreshes the 20+ curated global sources from the source catalog.
    """
    seeded_count = 0
    updated_count = 0

    for item in CURATED_SOURCES:
        stmt = select(Source).where(Source.id == item["id"])
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            # Update existing
            for k, v in item.items():
                setattr(existing, k, v)
            updated_count += 1
        else:
            # Insert new
            new_source = Source(**item)
            db.add(new_source)
            seeded_count += 1

    await db.commit()
    return {
        "status": "success",
        "sources_seeded": seeded_count,
        "sources_updated": updated_count,
        "total_catalog_size": len(CURATED_SOURCES)
    }
