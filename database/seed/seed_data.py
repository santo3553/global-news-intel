"""
Deterministic Seed Data Generator for Global News Intelligence.
Fulfills Section 35: Demonstrates multi-source clustering, multi-country events,
varying importance scores, uncertain/developing reports, and deduplication.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import AsyncSessionLocal, async_engine, Base
from apps.api.app.models import Source, Article, Event, EventArticle
from workers.normalization.normalizer import (
    normalize_url,
    clean_text,
    compute_hashes
)
from workers.collector.sources_catalog import CURATED_SOURCES


async def seed_database():
    print("--> Initializing tables and seeding deterministic news data...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Seed Sources
        print("--> Seeding curated sources catalog...")
        for src_data in CURATED_SOURCES:
            existing = (await session.execute(select(Source).where(Source.id == src_data["id"]))).scalar_one_or_none()
            if not existing:
                source = Source(**src_data)
                session.add(source)
        await session.commit()

        now = datetime.now(timezone.utc)

        # 2. Scenarios and Events
        scenarios = [
            # SCENARIO 1: Major Natural Disaster (Multiple Sources, High Impact, Japan)
            {
                "event": {
                    "id": "evt-japan-quake-2026",
                    "canonical_title": "Magnitude 7.1 Earthquake Strikes Miyazaki Prefecture, Southern Japan",
                    "summary": "A powerful magnitude 7.1 earthquake occurred off the eastern coast of Kyushu, Japan. Tsunami advisories were triggered for coastal areas with minor tsunami waves observed in Miyazaki and Kochi harbors. Multiple transport delays and local structural inspections underway.",
                    "category": "natural_disaster",
                    "subcategory": "earthquake",
                    "latitude": 31.8,
                    "longitude": 131.4,
                    "country": "Japan",
                    "admin_region": "Kyushu",
                    "city": "Miyazaki",
                    "location_confidence": 0.98,
                    "importance_score": 8.9,
                    "confidence_score": 0.95,
                    "human_impact_score": 8.5,
                    "global_impact_score": 7.8,
                    "economic_impact_score": 7.0,
                    "political_impact_score": 5.0,
                    "novelty_score": 8.2,
                    "development_velocity_score": 9.0,
                    "source_coverage_score": 9.5,
                    "first_seen_at": now - timedelta(hours=3),
                    "last_updated_at": now - timedelta(minutes=15),
                    "status": "developing"
                },
                "articles": [
                    {
                        "id": "art-reuters-quake-01",
                        "source_id": "src-reuters-world",
                        "title": "Strong 7.1 magnitude quake strikes off southern Japan; tsunami advisory issued",
                        "url": "https://www.reuters.com/world/asia-pacific/strong-quake-southern-japan-tsunami-advisory-2026",
                        "author": "Kiyoshi Takenaka",
                        "published_at": now - timedelta(hours=3),
                        "raw_content": "A magnitude 7.1 earthquake struck off southern Japan on Monday, prompting the meteorological agency to issue tsunami advisories for coastal regions of Kyushu.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-nhk-quake-02",
                        "source_id": "src-nhk-world",
                        "title": "M7.1 earthquake hits off Miyazaki Coast; JMA urges vigilance for aftershocks",
                        "url": "https://www3.nhk.or.jp/nhkworld/en/news/2026-miyazaki-earthquake-m71/",
                        "author": "NHK Newsroom",
                        "published_at": now - timedelta(hours=2, minutes=45),
                        "raw_content": "The Japan Meteorological Agency says an M7.1 earthquake registered an upper 5 on the seismic intensity scale in Miyazaki. Coastal waves up to 50cm were recorded.",
                        "relationship_type": "corroborating"
                    },
                    {
                        "id": "art-bbc-quake-03",
                        "source_id": "src-bbc-world",
                        "title": "Japan earthquake: Tsunami warnings lifted after magnitude 7.1 tremor",
                        "url": "https://www.bbc.com/news/world-asia-69482910?utm_source=twitter&utm_medium=social",
                        "author": "Rupert Wingfield-Hayes",
                        "published_at": now - timedelta(hours=1, minutes=30),
                        "raw_content": "Japanese authorities have lifted all tsunami advisories hours after a magnitude 7.1 earthquake struck off the southern island of Kyushu with no immediate reports of major damage.",
                        "relationship_type": "update"
                    },
                    {
                        "id": "art-ap-quake-04",
                        "source_id": "src-ap-top",
                        "title": "Japan assessing nuclear plant safety following magnitude 7.1 Kyushu tremor",
                        "url": "https://apnews.com/article/japan-earthquake-kyushu-nuclear-safety-2026",
                        "author": "Mari Yamaguchi",
                        "published_at": now - timedelta(hours=1),
                        "raw_content": "Japan's Nuclear Regulation Authority confirmed that Sendai and Genkai nuclear plants in Kyushu reported zero abnormalities following the magnitude 7.1 offshore earthquake.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 2: Global Climate Accord (Geneva, Switzerland - Multi-source Geopolitical)
            {
                "event": {
                    "id": "evt-geneva-climate-2026",
                    "canonical_title": "142 Nations Ratify Accelerated Clean Energy Mandate at Geneva Summit",
                    "summary": "Delegates at the extraordinary UN Climate Conference in Geneva concluded negotiations on a legally binding pact accelerating clean energy transition deadlines to 2035 with a dedicated $150B adaptation fund.",
                    "category": "politics",
                    "subcategory": "diplomacy",
                    "latitude": 46.2,
                    "longitude": 6.14,
                    "country": "Switzerland",
                    "admin_region": "Geneva",
                    "city": "Geneva",
                    "location_confidence": 0.99,
                    "importance_score": 8.3,
                    "confidence_score": 0.92,
                    "human_impact_score": 7.5,
                    "global_impact_score": 9.0,
                    "economic_impact_score": 8.2,
                    "political_impact_score": 8.8,
                    "novelty_score": 7.5,
                    "development_velocity_score": 6.5,
                    "source_coverage_score": 9.0,
                    "first_seen_at": now - timedelta(hours=8),
                    "last_updated_at": now - timedelta(hours=2),
                    "status": "active"
                },
                "articles": [
                    {
                        "id": "art-dw-climate-01",
                        "source_id": "src-dw-world",
                        "title": "Geneva Climate Summit: Nations clinch surprise consensus on 2035 clean power pact",
                        "url": "https://www.dw.com/en/geneva-climate-summit-breakthrough-2035-accord/a-7182901",
                        "author": "Tim Schauenberg",
                        "published_at": now - timedelta(hours=7, minutes=30),
                        "raw_content": "Negotiators in Geneva concluded 48 hours of uninterrupted deliberations, reaching a landmark compromise on global clean power benchmarks and transition financing.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-france24-climate-02",
                        "source_id": "src-france24-en",
                        "title": "Diplomats hail historic breakthrough in Geneva as 142 countries sign clean energy treaty",
                        "url": "https://www.france24.com/en/environment/2026-geneva-summit-historic-agreement",
                        "author": "Claire Cohen",
                        "published_at": now - timedelta(hours=6),
                        "raw_content": "French and European Union representatives praised the new Geneva agreement as a decisive turning point in multi-lateral environmental governance.",
                        "relationship_type": "corroborating"
                    },
                    {
                        "id": "art-guardian-climate-03",
                        "source_id": "src-theguardian-world",
                        "title": "Geneva climate agreement: What was agreed and what it means for global energy",
                        "url": "https://www.theguardian.com/environment/2026/sep/geneva-climate-pact-analysis",
                        "author": "Fiona Harvey",
                        "published_at": now - timedelta(hours=4),
                        "raw_content": "An analysis of the Geneva Accord's binding 2035 provisions and the enforcement mechanisms designed to hold signatory governments accountable.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 3: Uncertain / Developing Story with Low Confidence (Baltic Grid Anomaly)
            {
                "event": {
                    "id": "evt-baltic-grid-2026",
                    "canonical_title": "Investigation Opened into Power Grid Telemetry Anomaly in Eastern Baltic",
                    "summary": "Regional transmission operators reported unexpected high-voltage oscillations along subsea electrical interconnectors. Initial speculation of physical tampering remains unconfirmed by maritime defense authorities.",
                    "category": "security",
                    "subcategory": "infrastructure",
                    "latitude": 56.95,
                    "longitude": 24.1,
                    "country": "Latvia",
                    "admin_region": "Vidzeme",
                    "city": "Riga",
                    "location_confidence": 0.70,
                    "importance_score": 6.8,
                    "confidence_score": 0.42,  # Deliberately low confidence
                    "human_impact_score": 5.0,
                    "global_impact_score": 6.5,
                    "economic_impact_score": 6.2,
                    "political_impact_score": 7.4,
                    "novelty_score": 8.0,
                    "development_velocity_score": 7.0,
                    "source_coverage_score": 5.0,
                    "first_seen_at": now - timedelta(hours=2),
                    "last_updated_at": now - timedelta(minutes=30),
                    "status": "developing"
                },
                "articles": [
                    {
                        "id": "art-euronews-baltic-01",
                        "source_id": "src-euronews-en",
                        "title": "Baltic grid operators investigate electrical fluctuations; sabotage unconfirmed",
                        "url": "https://www.euronews.com/2026/baltic-power-interconnector-probe",
                        "author": "Euronews Riga Bureau",
                        "published_at": now - timedelta(hours=2),
                        "raw_content": "Transmission system operators in the Baltic region are investigating unusual telemetry spikes. Officials caution against jumping to conclusions regarding external sabotage.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 4: Major Scientific Discovery (Single Source, High Confidence)
            {
                "event": {
                    "id": "evt-jwst-exoplanet-2026",
                    "canonical_title": "James Webb Telescope Detects Stable Water Vapor Atmosphere on Rocky Exoplanet",
                    "summary": "NASA's James Webb Space Telescope has confirmed the presence of a stable, non-primordial water vapor atmosphere surrounding a temperate rocky world located 40 light-years away, marking an astronomical first.",
                    "category": "science",
                    "subcategory": "astronomy",
                    "latitude": 38.88,
                    "longitude": -77.02,
                    "country": "United States",
                    "admin_region": "District of Columbia",
                    "city": "Washington",
                    "location_confidence": 0.95,
                    "importance_score": 7.6,
                    "confidence_score": 0.97,
                    "human_impact_score": 4.0,
                    "global_impact_score": 8.8,
                    "economic_impact_score": 3.0,
                    "political_impact_score": 4.0,
                    "novelty_score": 9.8,
                    "development_velocity_score": 4.0,
                    "source_coverage_score": 7.5,
                    "first_seen_at": now - timedelta(hours=14),
                    "last_updated_at": now - timedelta(hours=6),
                    "status": "active"
                },
                "articles": [
                    {
                        "id": "art-ap-jwst-01",
                        "source_id": "src-ap-top",
                        "title": "NASA's Webb telescope confirms water vapor on Earth-sized rocky exoplanet",
                        "url": "https://apnews.com/article/webb-telescope-exoplanet-atmosphere-water-2026",
                        "author": "Marcia Dunn",
                        "published_at": now - timedelta(hours=14),
                        "raw_content": "Astronomers analyzing spectroscopic transmission data from NASA's Webb Space Telescope confirmed clear atmospheric signatures of water vapor on a rocky exoplanet.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 5: Latin American Economic Expansion
            {
                "event": {
                    "id": "evt-mercosur-trade-2026",
                    "canonical_title": "Mercosur and Southeast Asian Bloc Sign Comprehensive Free Trade Pact",
                    "summary": "South American trade group Mercosur concluded a multi-year bilateral agreement with ASEAN member states in Buenos Aires, eliminating tariffs on agricultural exports and industrial machinery.",
                    "category": "economy",
                    "subcategory": "trade",
                    "latitude": -34.60,
                    "longitude": -58.38,
                    "country": "Argentina",
                    "admin_region": "Buenos Aires",
                    "city": "Buenos Aires",
                    "location_confidence": 0.95,
                    "importance_score": 6.9,
                    "confidence_score": 0.88,
                    "human_impact_score": 6.2,
                    "global_impact_score": 7.2,
                    "economic_impact_score": 8.5,
                    "political_impact_score": 6.8,
                    "novelty_score": 6.5,
                    "development_velocity_score": 5.0,
                    "source_coverage_score": 7.8,
                    "first_seen_at": now - timedelta(hours=18),
                    "last_updated_at": now - timedelta(hours=5),
                    "status": "active"
                },
                "articles": [
                    {
                        "id": "art-mercopress-trade-01",
                        "source_id": "src-mercopress-en",
                        "title": "Mercosur concludes historic commercial expansion treaty in Buenos Aires",
                        "url": "https://en.mercopress.com/2026/09/14/mercosur-asean-trade-pact-signed",
                        "author": "Mercopress Staff",
                        "published_at": now - timedelta(hours=18),
                        "raw_content": "Foreign ministers from Brazil, Argentina, Uruguay, and Paraguay signed the final bilateral trade protocols with Southeast Asian partners today in Buenos Aires.",
                        "relationship_type": "primary"
                    }
                ]
            }
        ]

        # Insert Events and Articles
        for item in scenarios:
            evt_data = item["event"]
            existing_event = (await session.execute(select(Event).where(Event.id == evt_data["id"]))).scalar_one_or_none()
            if not existing_event:
                event = Event(**evt_data)
                session.add(event)
                await session.flush()
            else:
                event = existing_event

            for art_data in item["articles"]:
                rel_type = art_data.pop("relationship_type", "corroborating")
                canonical_url = normalize_url(art_data["url"])
                clean_t = clean_text(art_data["title"])
                clean_c = clean_text(art_data["raw_content"])
                t_hash, c_hash = compute_hashes(clean_t, clean_c)

                existing_article = (await session.execute(select(Article).where(Article.id == art_data["id"]))).scalar_one_or_none()
                if not existing_article:
                    article = Article(
                        id=art_data["id"],
                        source_id=art_data["source_id"],
                        title=clean_t,
                        url=art_data["url"],
                        canonical_url=canonical_url,
                        author=art_data.get("author"),
                        published_at=art_data.get("published_at"),
                        fetched_at=now,
                        language="en",
                        raw_content=art_data["raw_content"],
                        cleaned_content=clean_c,
                        content_hash=c_hash,
                        title_hash=t_hash,
                        processing_status="clustered"
                    )
                    session.add(article)
                    await session.flush()
                else:
                    article = existing_article

                # Link Event to Article
                existing_link = (await session.execute(
                    select(EventArticle).where(
                        EventArticle.event_id == event.id,
                        EventArticle.article_id == article.id
                    )
                )).scalar_one_or_none()

                if not existing_link:
                    link = EventArticle(
                        event_id=event.id,
                        article_id=article.id,
                        similarity_score=0.92,
                        relationship_type=rel_type,
                        created_at=now
                    )
                    session.add(link)

        await session.commit()
        print("--> Seed data generated successfully! 5 Events and 10 Articles created across multiple continents.")


if __name__ == "__main__":
    asyncio.run(seed_database())
