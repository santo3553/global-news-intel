"""
FastAPI Routes for Pipeline Orchestration & Daemon Control.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import get_db
from workers.orchestrator.pipeline_orchestrator import (
    PipelineOrchestrator,
    get_pipeline_daemon
)

logger = logging.getLogger("gni.routes.pipeline")

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])


@router.post("/run")
async def trigger_pipeline_run(
    max_feeds: Optional[int] = Query(None, description="Max feeds to check in this run"),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers an immediate autonomous pipeline cycle across all active sources.
    Executes: Ingestion -> Deduplication -> AI Extraction -> Geocoding -> Clustering -> Ranking -> Decay.
    """
    orchestrator = PipelineOrchestrator()
    telemetry = await orchestrator.run_cycle(session=db, max_feeds=max_feeds)
    return telemetry.to_dict()


@router.get("/status")
async def get_pipeline_status():
    """
    Returns current daemon status and metrics from the most recent processing cycle.
    """
    daemon = get_pipeline_daemon()
    return daemon.get_status()


@router.post("/daemon/start")
async def start_pipeline_daemon(
    interval_seconds: int = Query(900, description="Cycle interval in seconds (default 15 minutes)")
):
    """
    Starts the continuous background processing daemon loop.
    """
    daemon = get_pipeline_daemon(interval_seconds=interval_seconds)
    daemon.start()
    return {"message": "Pipeline daemon started", "status": daemon.get_status()}


@router.post("/daemon/stop")
async def stop_pipeline_daemon():
    """
    Halts the continuous background processing daemon loop.
    """
    daemon = get_pipeline_daemon()
    daemon.stop()
    return {"message": "Pipeline daemon stopped", "status": daemon.get_status()}
