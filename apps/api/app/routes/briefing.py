import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import get_db
from apps.api.app.schemas.briefing import IntelligenceBriefingResponse
from apps.api.app.services.briefing_service import BriefingService

logger = logging.getLogger("gni.routes.briefing")

router = APIRouter(prefix="/api/briefing", tags=["Intelligence Briefing"])


@router.get("", response_model=IntelligenceBriefingResponse, summary="Get executive global intelligence briefing")
async def get_briefing(
    limit_per_section: int = Query(4, ge=1, le=10, description="Max items per category section"),
    db: AsyncSession = Depends(get_db)
):
    """
    Answers: 'What should I read right now?'
    Synthesizes active global events into breaking alerts, geopolitical moves,
    humanitarian hazards, and economic disruptions.
    """
    return await BriefingService.generate_briefing(
        session=db,
        limit_per_section=limit_per_section
    )
