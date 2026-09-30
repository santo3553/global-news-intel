from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import get_db
from apps.api.app.models import Article
from apps.api.app.schemas.event import EventResponse, EventDetailResponse
from apps.api.app.schemas.briefing import EventTimelineResponse
from apps.api.app.services.event_service import EventService
from workers.clustering.clusterer import EventClusterer
from ai.providers.factory import get_ai_provider

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("", response_model=List[EventResponse], summary="List events with spatial bounding box and filters")
async def list_events(
    bbox: Optional[str] = Query(None, description="Bounding box filter in format 'minLng,minLat,maxLng,maxLat'"),
    category: Optional[str] = Query(None, description="Category filter (natural_disaster, politics, security, etc.)"),
    country: Optional[str] = Query(None, description="Country filter"),
    min_importance: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum importance score"),
    status: Optional[str] = Query(None, description="Event lifecycle status (active, developing, resolved)"),
    sort_by: str = Query("importance", description="Sort order (importance, confidence, velocity, recent)"),
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    Primary endpoint for the interactive world map:
    Returns events within a geographic bounding box and zoom level.
    """
    return await EventService.list_events(
        session=db,
        bbox=bbox,
        category=category,
        country=country,
        min_importance=min_importance,
        status=status,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )


@router.get("/top", response_model=List[EventResponse], summary="Get highest-ranked global events")
async def get_top_events(
    limit: int = Query(5, ge=1, le=25, description="Number of top events to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the top most important and high-confidence events globally for dashboard briefings.
    """
    return await EventService.list_events(
        session=db,
        status="active",
        limit=limit
    )


@router.get("/nearby", summary="Find events near coordinates")
async def get_nearby_events(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Longitude"),
    radius_km: float = Query(300.0, ge=1.0, le=5000.0, description="Search radius in kilometers"),
    limit: int = Query(15, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns events within radius_km of the specified coordinate, sorted by distance.
    """
    return await EventService.get_nearby_events(
        session=db,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        limit=limit
    )


@router.get("/search", response_model=List[EventResponse], summary="Full-text search events")
async def search_events(
    q: str = Query(..., min_length=1, description="Search term for title, summary, location, or category"),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search events by keyword across titles, summaries, countries, and categories.
    """
    return await EventService.search_events(session=db, query=q, limit=limit)


@router.get("/{event_id}", response_model=EventDetailResponse, summary="Get full event details with linked articles")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves single event details including associated corroborating articles, sources, and claims.
    """
    evt_detail = await EventService.get_event_detail(db, event_id)
    if not evt_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found"
        )
    return evt_detail


@router.get("/{event_id}/timeline", response_model=EventTimelineResponse, summary="Get event chronological timeline")
async def get_event_timeline(event_id: str, db: AsyncSession = Depends(get_db)):
    """
    Chronological progression of articles and updates that developed this event.
    """
    try:
        from apps.api.app.services.briefing_service import BriefingService
        return await BriefingService.get_event_timeline(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/cluster", summary="Run clustering cycle over unclustered articles")
async def trigger_clustering(
    limit: int = Query(25, ge=1, le=100, description="Max unclustered articles to evaluate"),
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates articles in 'extracted' or 'pending' status, clusters related articles
    into existing events or initializes new events.
    """
    clusterer = EventClusterer()
    ai_provider = get_ai_provider()

    # Find articles needing clustering
    stmt = select(Article).where(Article.processing_status.in_(["extracted", "pending"])).limit(limit)
    res = await db.execute(stmt)
    articles = res.scalars().all()

    results = []
    for art in articles:
        content = art.cleaned_content or art.raw_content or art.title
        extracted_data = await ai_provider.extract_event(art.title, content)
        decision = await clusterer.cluster_article(db, art, extracted_data)
        results.append({
            "article_id": art.id,
            "decision": decision.to_dict()
        })

    return {
        "status": "completed",
        "articles_evaluated": len(articles),
        "results": results
    }


@router.post("/decay", summary="Trigger periodic velocity decay and lifecycle status transitions")
async def trigger_decay(
    max_events: int = Query(50, ge=1, le=200, description="Max events to evaluate for decay"),
    db: AsyncSession = Depends(get_db)
):
    """
    Applies temporal decay to development velocity and transitions stale events.
    """
    from workers.ranking.ranking_worker import EventRankingWorker
    updated = await EventRankingWorker.batch_decay_events(db, max_events=max_events)
    return {
        "status": "completed",
        "events_updated": updated
    }

