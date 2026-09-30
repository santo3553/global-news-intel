"""
Tests for Pipeline Orchestrator, Autonomous Daemon, and Pipeline Endpoints.
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models import Source, Article, Event
from workers.orchestrator.pipeline_orchestrator import (
    PipelineOrchestrator,
    PipelineDaemon,
    get_pipeline_daemon
)

SAMPLE_FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Global Test News</title>
    <link>https://testwire.com</link>
    <description>Reliable global dispatches</description>
    <item>
      <title>Massive Subsea Fiber Cable Disruption in North Atlantic</title>
      <link>https://testwire.com/cable-outage-01</link>
      <description>Maritime engineers deploy repair vessels following severe subsea cable severed west of Ireland.</description>
      <pubDate>Mon, 30 Sep 2026 12:00:00 GMT</pubDate>
      <author>Claire O'Connor</author>
    </item>
    <item>
      <title>Reykjavik Emergency Teams Respond to Coastal Surge Alerts</title>
      <link>https://testwire.com/surge-alert-02</link>
      <description>Iceland civil protection advises harbor caution amid strong tidal surges.</description>
      <pubDate>Mon, 30 Sep 2026 12:30:00 GMT</pubDate>
      <author>Arnar Jonsson</author>
    </item>
  </channel>
</rss>
"""


@pytest.mark.asyncio
async def test_pipeline_cycle_execution_and_clustering(async_db: AsyncSession):
    # Setup test source
    source = Source(
        id="src-orch-test",
        name="Global Test Wire",
        domain="testwire.com",
        feed_url="https://testwire.com/rss",
        active=True
    )
    async_db.add(source)
    await async_db.commit()

    orchestrator = PipelineOrchestrator()

    # Mock network fetch to return test RSS feed
    with patch.object(orchestrator.collector, "fetch_feed", return_value=SAMPLE_FEED_XML):
        telemetry = await orchestrator.run_cycle(session=async_db, max_feeds=1)

        assert telemetry.status in ("success", "partial_failure")
        assert telemetry.sources_checked >= 1
        assert telemetry.articles_fetched == 2
        assert telemetry.articles_inserted == 2
        assert telemetry.articles_processed == 2
        assert telemetry.events_created >= 1

        # Verify articles exist and were clustered
        res_arts = await async_db.execute(select(Article).where(Article.source_id == "src-orch-test"))
        arts = list(res_arts.scalars().all())
        assert len(arts) == 2
        for art in arts:
            assert art.processing_status == "clustered"
            assert art.embedding is not None

        # Verify event was formed
        res_evts = await async_db.execute(select(Event))
        evts = list(res_evts.scalars().all())
        assert len(evts) >= 1


@pytest.mark.asyncio
async def test_pipeline_cycle_deduplication(async_db: AsyncSession):
    source = Source(
        id="src-orch-dedup",
        name="Dedup Test Wire",
        domain="testwire.com",
        feed_url="https://testwire.com/rss",
        active=True
    )
    async_db.add(source)
    await async_db.commit()

    orchestrator = PipelineOrchestrator()

    with patch.object(orchestrator.collector, "fetch_feed", return_value=SAMPLE_FEED_XML):
        # First cycle: inserts articles
        t1 = await orchestrator.run_cycle(session=async_db, max_feeds=1)
        assert t1.articles_inserted == 2

        # Second cycle with exact same feed: skips duplicates
        t2 = await orchestrator.run_cycle(session=async_db, max_feeds=1)
        assert t2.articles_inserted == 0
        assert t2.duplicates_skipped == 2


@pytest.mark.asyncio
async def test_pipeline_api_endpoints(async_db: AsyncSession, client: AsyncClient):
    # 1. Check initial status
    res_status = await client.get("/api/pipeline/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert "daemon_active" in status_data
    assert "total_cycles_run" in status_data

    # 2. Trigger on-demand pipeline run with mock feed
    with patch("workers.collector.rss_collector.RSSCollector.fetch_feed", return_value=SAMPLE_FEED_XML):
        res_run = await client.post("/api/pipeline/run?max_feeds=1")
        assert res_run.status_code == 200
        run_data = res_run.json()
        assert "sources_checked" in run_data
        assert "duration_seconds" in run_data
        assert "articles_fetched" in run_data

    # 3. Test daemon start / stop
    res_start = await client.post("/api/pipeline/daemon/start?interval_seconds=120")
    assert res_start.status_code == 200
    start_data = res_start.json()
    assert start_data["status"]["daemon_active"] is True

    res_stop = await client.post("/api/pipeline/daemon/stop")
    assert res_stop.status_code == 200
    stop_data = res_stop.json()
    assert stop_data["status"]["daemon_active"] is False
