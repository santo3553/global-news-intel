"""
Autonomous Pipeline Orchestrator & Live Processing Daemon.
Orchestrates: COLLECTION → DEDUPLICATION → AI EXTRACTION → GEOCODING → CLUSTERING → RANKING → DECAY.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.config import settings
from apps.api.app.database import AsyncSessionLocal
from apps.api.app.models import Source, Article, Event
from workers.collector.rss_collector import RSSCollector
from workers.collector.sources_catalog import CURATED_SOURCES
from workers.normalization.deduplicator import Deduplicator
from workers.extraction.geocoder import Geocoder
from workers.embeddings.embedding_engine import EmbeddingEngine
from workers.clustering.clusterer import EventClusterer
from workers.ranking.ranking_worker import EventRankingWorker
from ai.providers.factory import get_ai_provider

logger = logging.getLogger("gni.orchestrator")


@dataclass
class PipelineTelemetry:
    started_at: str
    completed_at: str
    duration_seconds: float
    sources_checked: int = 0
    articles_fetched: int = 0
    articles_inserted: int = 0
    duplicates_skipped: int = 0
    articles_processed: int = 0
    events_created: int = 0
    events_updated: int = 0
    events_decayed: int = 0
    status: str = "success"
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PipelineOrchestrator:
    """
    Orchestrates the entire local-first Global News Intelligence processing pipeline.
    """

    def __init__(self):
        self.deduplicator = Deduplicator(
            near_duplicate_threshold=settings.DEDUPLICATION_HASH_THRESHOLD,
            time_window_hours=settings.MAX_CLUSTER_TIME_WINDOW_HOURS
        )
        self.collector = RSSCollector(deduplicator=self.deduplicator)
        self.ai_provider = get_ai_provider()
        self.geocoder = Geocoder()
        self.embedding_engine = EmbeddingEngine()
        self.clusterer = EventClusterer()
        self.ranking_worker = EventRankingWorker()

    async def ensure_sources_seeded(self, session: AsyncSession) -> List[Source]:
        """Ensures at least curated sources are in the database."""
        res = await session.execute(select(Source).where(Source.active.is_(True)))
        sources = list(res.scalars().all())
        if not sources:
            logger.info("No active sources found. Auto-seeding curated sources catalog...")
            for src_data in CURATED_SOURCES:
                existing = (await session.execute(select(Source).where(Source.id == src_data["id"]))).scalar_one_or_none()
                if not existing:
                    session.add(Source(**src_data))
            await session.commit()
            res = await session.execute(select(Source).where(Source.active.is_(True)))
            sources = list(res.scalars().all())
        return sources

    async def run_cycle(
        self,
        session: AsyncSession,
        max_feeds: Optional[int] = None,
        max_articles_per_feed: int = 15,
        max_extraction_batch: int = 30
    ) -> PipelineTelemetry:
        """
        Executes one full autonomous ingestion and intelligence synthesis cycle.
        """
        start_time = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()
        errors: List[str] = []

        sources_checked = 0
        articles_fetched = 0
        articles_inserted = 0
        duplicates_skipped = 0
        articles_processed = 0
        events_created = 0
        events_updated = 0
        events_decayed = 0

        logger.info("=== STARTING AUTONOMOUS PIPELINE CYCLE ===")

        # -------------------------------------------------------------
        # STEP 1: Sources Ingestion & Deduplication
        # -------------------------------------------------------------
        try:
            sources = await self.ensure_sources_seeded(session)
            if max_feeds:
                sources = sources[:max_feeds]

            sources_checked = len(sources)
            logger.info("Polling %d active feeds for new dispatches...", sources_checked)

            for source in sources:
                try:
                    feed_stats = await self.collector.process_source(
                        session=session,
                        source=source,
                        max_articles=max_articles_per_feed
                    )
                    articles_fetched += feed_stats.get("fetched", 0)
                    articles_inserted += feed_stats.get("inserted", 0)
                    duplicates_skipped += feed_stats.get("deduplicated", 0)
                except Exception as feed_err:
                    err_msg = f"Source [{source.id}] fetch error: {feed_err}"
                    logger.warning(err_msg)
                    errors.append(err_msg)

        except Exception as step1_err:
            err_msg = f"Step 1 (Ingestion) fatal error: {step1_err}"
            logger.error(err_msg)
            errors.append(err_msg)

        # -------------------------------------------------------------
        # STEP 2: AI Extraction, Geocoding & Embeddings
        # -------------------------------------------------------------
        try:
            # Query newly inserted articles that are pending extraction
            stmt = (
                select(Article)
                .where(Article.processing_status == "pending")
                .order_by(Article.published_at.desc())
                .limit(max_extraction_batch)
            )
            res = await session.execute(stmt)
            pending_articles = list(res.scalars().all())

            logger.info("Extracting & geocoding %d pending articles...", len(pending_articles))

            for article in pending_articles:
                try:
                    content_for_ai = article.cleaned_content or article.raw_content or article.title

                    # AI Structured Extraction
                    extracted_data = await self.ai_provider.extract_event(
                        title=article.title,
                        text=content_for_ai
                    )

                    # Coordinate Grounding & Spatial Disambiguation
                    resolved_loc = self.geocoder.resolve(
                        raw_name=extracted_data.location.name,
                        country_hint=extracted_data.location.country,
                        text_context=content_for_ai[:1000],
                        llm_lat=extracted_data.location.latitude,
                        llm_lng=extracted_data.location.longitude
                    )

                    # Dense Semantic Vector Embeddings
                    embedding_text = f"{article.title} {extracted_data.category} {resolved_loc.name} {content_for_ai[:400]}"
                    embedding = await self.embedding_engine.embed_text(embedding_text)

                    # Update Article
                    article.embedding = embedding
                    article.processing_status = "extracted"
                    article.updated_at = datetime.now(timezone.utc)
                    await session.flush()

                    # -------------------------------------------------------------
                    # STEP 3: Multi-Signal Event Clustering & Lifecycle
                    # -------------------------------------------------------------
                    clustering_decision = await self.clusterer.cluster_article(
                        session=session,
                        article=article,
                        extracted_data=extracted_data
                    )

                    if clustering_decision.action == "created":
                        events_created += 1
                        logger.info("Created new Event [%s] from article [%s]", clustering_decision.event_id, article.id)
                    elif clustering_decision.action == "merged":
                        events_updated += 1
                        logger.info("Merged article [%s] into Event [%s]", article.id, clustering_decision.event_id)

                    article.processing_status = "clustered"
                    articles_processed += 1
                    await session.commit()

                except Exception as art_err:
                    err_msg = f"Failed processing article [{article.id}]: {art_err}"
                    logger.error(err_msg)
                    errors.append(err_msg)
                    article.processing_status = "failed"
                    await session.commit()

        except Exception as step2_err:
            err_msg = f"Step 2/3 (Extraction & Clustering) error: {step2_err}"
            logger.error(err_msg)
            errors.append(err_msg)

        # -------------------------------------------------------------
        # STEP 4: Periodic Velocity Decay & Ranking Maintenance
        # -------------------------------------------------------------
        try:
            events_decayed = await self.ranking_worker.batch_decay_events(session)
            logger.info("Decayed velocity on %d active events", events_decayed)
        except Exception as step4_err:
            err_msg = f"Step 4 (Decay) error: {step4_err}"
            logger.error(err_msg)
            errors.append(err_msg)

        duration = round(time.time() - start_time, 2)
        status_label = "partial_failure" if errors else "success"

        telemetry = PipelineTelemetry(
            started_at=start_iso,
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_seconds=duration,
            sources_checked=sources_checked,
            articles_fetched=articles_fetched,
            articles_inserted=articles_inserted,
            duplicates_skipped=duplicates_skipped,
            articles_processed=articles_processed,
            events_created=events_created,
            events_updated=events_updated,
            events_decayed=events_decayed,
            status=status_label,
            errors=errors[:5]  # Cap error samples
        )

        logger.info(
            "=== PIPELINE CYCLE FINISHED in %.2fs: %d inserted, %d deduplicated, %d extracted, %d new events, %d merged ===",
            duration,
            articles_inserted,
            duplicates_skipped,
            articles_processed,
            events_created,
            events_updated
        )
        return telemetry


class PipelineDaemon:
    """
    Background daemon service running periodic pipeline cycles.
    """

    def __init__(self, interval_seconds: int = 900):
        self.interval_seconds = interval_seconds
        self.orchestrator = PipelineOrchestrator()
        self._task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self.last_telemetry: Optional[PipelineTelemetry] = None
        self.last_run_at: Optional[str] = None
        self.total_cycles_run: int = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self):
        """Starts background loop if not already running."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Pipeline daemon started (interval=%d seconds)", self.interval_seconds)

    def stop(self):
        """Stops background loop."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Pipeline daemon stopped.")

    async def _run_loop(self):
        while self._is_running:
            try:
                await self.trigger_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Daemon cycle error: %s", e)

            # Sleep until next scheduled cycle
            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

    async def trigger_cycle(self, max_feeds: Optional[int] = None) -> PipelineTelemetry:
        """Runs a cycle immediately on demand."""
        async with AsyncSessionLocal() as session:
            telemetry = await self.orchestrator.run_cycle(session, max_feeds=max_feeds)
            self.last_telemetry = telemetry
            self.last_run_at = telemetry.completed_at
            self.total_cycles_run += 1
            return telemetry

    def get_status(self) -> Dict[str, Any]:
        return {
            "daemon_active": self._is_running,
            "interval_seconds": self.interval_seconds,
            "total_cycles_run": self.total_cycles_run,
            "last_run_at": self.last_run_at,
            "last_telemetry": self.last_telemetry.to_dict() if self.last_telemetry else None
        }


# Global Singleton Daemon instance
_daemon_instance: Optional[PipelineDaemon] = None


def get_pipeline_daemon(interval_seconds: int = 900) -> PipelineDaemon:
    global _daemon_instance
    if _daemon_instance is None:
        _daemon_instance = PipelineDaemon(interval_seconds=interval_seconds)
    return _daemon_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("--> Running ad-hoc pipeline orchestrator cycle...")

    async def main():
        daemon = get_pipeline_daemon()
        telemetry = await daemon.trigger_cycle()
        print("--> Ad-hoc cycle complete:", telemetry.to_dict())

    asyncio.run(main())
