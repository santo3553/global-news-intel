"""
Deterministic Seed Data Generator for Global News Intelligence.
Fulfills Section 24 & 25: Demonstrates multi-source clustering, multi-country events,
varying importance scores, uncertain/developing reports, deduplication, and named entities.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.database import AsyncSessionLocal, async_engine, Base
from apps.api.app.models import Source, Article, Event, EventArticle, Entity, EventEntity
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
        # 1. Seed Sources Catalog
        print("--> Seeding curated sources catalog...")
        for src_data in CURATED_SOURCES:
            existing = (await session.execute(select(Source).where(Source.id == src_data["id"]))).scalar_one_or_none()
            if not existing:
                source = Source(**src_data)
                session.add(source)
        await session.commit()

        now = datetime.now(timezone.utc)

        # 2. Comprehensive Global Intelligence Scenarios (15 distinct events)
        scenarios = [
            # SCENARIO 1: Major Natural Disaster (Multiple Sources, High Impact, Japan)
            {
                "event": {
                    "id": "evt-japan-quake-2026",
                    "canonical_title": "Magnitude 7.1 Offshore Earthquake Strikes Miyazaki Prefecture, Southern Japan",
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
                "entities": [
                    {"name": "Japan Meteorological Agency", "type": "organization"},
                    {"name": "Kyushu Electric Power", "type": "organization"},
                    {"name": "Miyazaki Prefecture", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-reuters-quake-01",
                        "source_id": "src-reuters-world",
                        "title": "Strong 7.1 magnitude quake strikes off southern Japan; tsunami advisory issued",
                        "url": "https://www.reuters.com/world/asia-pacific/",
                        "author": "Kiyoshi Takenaka",
                        "published_at": now - timedelta(hours=3),
                        "raw_content": "A magnitude 7.1 earthquake struck off southern Japan on Monday, prompting the meteorological agency to issue tsunami advisories for coastal regions of Kyushu.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-nhk-quake-02",
                        "source_id": "src-nhk-world",
                        "title": "M7.1 earthquake hits off Miyazaki Coast; JMA urges vigilance for aftershocks",
                        "url": "https://www3.nhk.or.jp/nhkworld/en/news/",
                        "author": "NHK Newsroom",
                        "published_at": now - timedelta(hours=2, minutes=45),
                        "raw_content": "The Japan Meteorological Agency says an M7.1 earthquake registered an upper 5 on the seismic intensity scale in Miyazaki. Coastal waves up to 50cm were recorded.",
                        "relationship_type": "corroborating"
                    },
                    {
                        "id": "art-bbc-quake-03",
                        "source_id": "src-bbc-world",
                        "title": "Japan earthquake: Tsunami warnings lifted after magnitude 7.1 tremor",
                        "url": "https://www.bbc.com/news/world-asia",
                        "author": "Rupert Wingfield-Hayes",
                        "published_at": now - timedelta(hours=1, minutes=30),
                        "raw_content": "Japanese authorities have lifted all tsunami advisories hours after a magnitude 7.1 earthquake struck off the southern island of Kyushu with no immediate reports of major damage.",
                        "relationship_type": "update"
                    },
                    {
                        "id": "art-ap-quake-04",
                        "source_id": "src-ap-top",
                        "title": "Japan assessing nuclear plant safety following magnitude 7.1 Kyushu tremor",
                        "url": "https://apnews.com/hub/earthquakes",
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
                "entities": [
                    {"name": "United Nations", "type": "organization"},
                    {"name": "European Commission", "type": "organization"},
                    {"name": "Geneva", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-dw-climate-01",
                        "source_id": "src-dw-world",
                        "title": "Geneva Climate Summit: Nations clinch surprise consensus on 2035 clean power pact",
                        "url": "https://www.dw.com/en/climate-change/s-30842",
                        "author": "Tim Schauenberg",
                        "published_at": now - timedelta(hours=7, minutes=30),
                        "raw_content": "Negotiators in Geneva concluded 48 hours of uninterrupted deliberations, reaching a landmark compromise on global clean power benchmarks and transition financing.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-france24-climate-02",
                        "source_id": "src-france24-en",
                        "title": "Diplomats hail historic breakthrough in Geneva as 142 countries sign clean energy treaty",
                        "url": "https://www.france24.com/en/environment/",
                        "author": "Claire Cohen",
                        "published_at": now - timedelta(hours=6),
                        "raw_content": "French and European Union representatives praised the new Geneva agreement as a decisive turning point in multi-lateral environmental governance.",
                        "relationship_type": "corroborating"
                    },
                    {
                        "id": "art-guardian-climate-03",
                        "source_id": "src-theguardian-world",
                        "title": "Geneva climate agreement: What was agreed and what it means for global energy",
                        "url": "https://www.theguardian.com/environment/climate-crisis",
                        "author": "Fiona Harvey",
                        "published_at": now - timedelta(hours=4),
                        "raw_content": "An analysis of the Geneva Accord's binding 2035 provisions and the enforcement mechanisms designed to hold signatory governments accountable.",
                        "relationship_type": "corroborating"
                    },
                    {
                        "id": "art-ap-climate-04",
                        "source_id": "src-ap-top",
                        "title": "Global financial markets rally following Geneva clean power accord announcement",
                        "url": "https://apnews.com/hub/climate-and-environment",
                        "author": "David McHugh",
                        "published_at": now - timedelta(hours=2),
                        "raw_content": "Renewable utility equities and green bond indices rose sharply across European and Asian trading sessions following the Geneva accord.",
                        "relationship_type": "update"
                    }
                ]
            },

            # SCENARIO 3: Red Sea Maritime Security Incident (Multi-Source Geopolitical Conflict)
            {
                "event": {
                    "id": "evt-redsea-corridor-2026",
                    "canonical_title": "Commercial Vessel Escorts Mobilized Following Drone Interception in Southern Red Sea",
                    "summary": "Multinational maritime naval coalition intercepted two surface drones near the Bab el-Mandeb strait. Commercial carriers re-evaluated transit advisories with container freight futures climbing 4.5% on global maritime exchanges.",
                    "category": "security",
                    "subcategory": "maritime",
                    "latitude": 12.8,
                    "longitude": 43.3,
                    "country": "Yemen",
                    "admin_region": "Bab el-Mandeb",
                    "city": "Al Hudaydah",
                    "location_confidence": 0.94,
                    "importance_score": 8.4,
                    "confidence_score": 0.93,
                    "human_impact_score": 6.8,
                    "global_impact_score": 8.6,
                    "economic_impact_score": 8.8,
                    "political_impact_score": 8.5,
                    "novelty_score": 7.0,
                    "development_velocity_score": 8.5,
                    "source_coverage_score": 9.2,
                    "first_seen_at": now - timedelta(hours=5),
                    "last_updated_at": now - timedelta(hours=1),
                    "status": "developing"
                },
                "entities": [
                    {"name": "International Maritime Organization", "type": "organization"},
                    {"name": "Combined Maritime Forces", "type": "organization"},
                    {"name": "Red Sea Shipping Corridor", "type": "concept"}
                ],
                "articles": [
                    {
                        "id": "art-aljazeera-redsea-01",
                        "source_id": "src-aljazeera-en",
                        "title": "Coalition warships intercept hostile drones targeting Red Sea shipping lanes",
                        "url": "https://www.aljazeera.com/where/middle-east/",
                        "author": "Al Jazeera Staff",
                        "published_at": now - timedelta(hours=5),
                        "raw_content": "Naval forces in the southern Red Sea repelled unmanned aerial craft approaching international commercial shipping vessels off the coast of Yemen.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-bbc-redsea-02",
                        "source_id": "src-bbc-world",
                        "title": "Red Sea tension flares as naval escort destroys explosive sea drone",
                        "url": "https://www.bbc.com/news/world-middle-east",
                        "author": "Jonathan Beale",
                        "published_at": now - timedelta(hours=3, minutes=30),
                        "raw_content": "A naval frigate successfully neutralized a fast-moving unmanned surface vessel in international waters, confirming no civilian casualties.",
                        "relationship_type": "corroborating"
                    },
                    {
                        "id": "art-reuters-redsea-03",
                        "source_id": "src-reuters-world",
                        "title": "Container insurance rates tick higher following latest Bab el-Mandeb incident",
                        "url": "https://www.reuters.com/world/middle-east/",
                        "author": "Jonathan Saul",
                        "published_at": now - timedelta(hours=2),
                        "raw_content": "Underwriters raised war risk premiums for commercial freighters entering the southern Red Sea corridor by 15 basis points.",
                        "relationship_type": "update"
                    }
                ]
            },

            # SCENARIO 4: Multi-Country Semiconductor Foundry Accord (Taiwan & Germany)
            {
                "event": {
                    "id": "evt-taiwan-semiconductor-2026",
                    "canonical_title": "Taiwan-European Semiconductor Foundry Accord Finalized for Dresden Fab",
                    "summary": "Advanced silicon chip consortium formalizes joint capital deployment of €11B for next-generation 2nm fabrication plant in Saxony, solidifying European automotive supply security.",
                    "category": "economy",
                    "subcategory": "semiconductors",
                    "latitude": 51.05,
                    "longitude": 13.73,
                    "country": "Germany",
                    "admin_region": "Saxony",
                    "city": "Dresden",
                    "location_confidence": 0.98,
                    "importance_score": 7.9,
                    "confidence_score": 0.91,
                    "human_impact_score": 3.5,
                    "global_impact_score": 8.4,
                    "economic_impact_score": 9.2,
                    "political_impact_score": 7.5,
                    "novelty_score": 7.8,
                    "development_velocity_score": 5.5,
                    "source_coverage_score": 8.5,
                    "first_seen_at": now - timedelta(hours=16),
                    "last_updated_at": now - timedelta(hours=4),
                    "status": "active"
                },
                "entities": [
                    {"name": "TSMC", "type": "organization"},
                    {"name": "Federal Ministry for Economic Affairs", "type": "organization"},
                    {"name": "Dresden", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-cna-semi-01",
                        "source_id": "src-cna-asia",
                        "title": "Taiwan tech delegation finalizes bilateral European semiconductor facility expansion",
                        "url": "https://www.channelnewsasia.com/business",
                        "author": "CNA Tech Desk",
                        "published_at": now - timedelta(hours=16),
                        "raw_content": "Industry executives from Hsinchu confirmed final clearance for the joint semiconductor manufacturing fab in Dresden.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-dw-semi-02",
                        "source_id": "src-dw-world",
                        "title": "Germany hails multi-billion euro Dresden microchip facility as milestone for EU industrial strategy",
                        "url": "https://www.dw.com/en/top-stories/s-9097",
                        "author": "Christoph Hasselbach",
                        "published_at": now - timedelta(hours=10),
                        "raw_content": "Federal officials in Berlin praised the €11 billion project, noting it will generate thousands of high-tech engineering jobs across Saxony.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 5: Iceland Reykjanes Volcanic Eruption
            {
                "event": {
                    "id": "evt-iceland-volcano-2026",
                    "canonical_title": "Fissure Eruption Opens on Reykjanes Peninsula Threatening Grindavik Access",
                    "summary": "A 1.2-kilometer volcanic fissure opened northeast of Mount Stora-Skogfell on the Reykjanes peninsula. Defensive earth barriers successfully diverted lava flows away from critical infrastructure.",
                    "category": "natural_disaster",
                    "subcategory": "volcano",
                    "latitude": 63.84,
                    "longitude": -22.43,
                    "country": "Iceland",
                    "admin_region": "Southern Peninsula",
                    "city": "Grindavik",
                    "location_confidence": 0.99,
                    "importance_score": 7.7,
                    "confidence_score": 0.96,
                    "human_impact_score": 7.0,
                    "global_impact_score": 6.8,
                    "economic_impact_score": 6.2,
                    "political_impact_score": 4.5,
                    "novelty_score": 7.4,
                    "development_velocity_score": 8.8,
                    "source_coverage_score": 8.0,
                    "first_seen_at": now - timedelta(hours=6),
                    "last_updated_at": now - timedelta(minutes=45),
                    "status": "developing"
                },
                "entities": [
                    {"name": "Icelandic Met Office", "type": "organization"},
                    {"name": "Keflavik International Airport", "type": "location"},
                    {"name": "Reykjanes", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-bbc-volcano-01",
                        "source_id": "src-bbc-world",
                        "title": "Volcanic fissure erupts on Iceland's Reykjanes peninsula; Grindavik evacuated",
                        "url": "https://www.bbc.com/news/world-europe",
                        "author": "Einar Sigurdsson",
                        "published_at": now - timedelta(hours=6),
                        "raw_content": "Lava is spewing from a newly opened fissure on the Reykjanes peninsula in south-west Iceland following intensive earthquake activity.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-euronews-volcano-02",
                        "source_id": "src-euronews-en",
                        "title": "Iceland volcano: Lava barriers protect geothermal plant as eruption stabilizes",
                        "url": "https://www.euronews.com/green",
                        "author": "Euronews Reykjavik Bureau",
                        "published_at": now - timedelta(hours=3),
                        "raw_content": "Civil protection teams confirmed protective berms successfully directed basalt flows safely away from Svartsengi powerplant.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 6: Multi-Country Nile Basin Water Treaty (Egypt, Sudan, Ethiopia)
            {
                "event": {
                    "id": "evt-horn-africa-nile-2026",
                    "canonical_title": "Tripartite Ministerial Protocol Concluded on Eastern Nile Water Sharing",
                    "summary": "Water and foreign ministers of Egypt, Ethiopia, and Sudan finalized a historic hydrological monitoring accord in Cairo, establishing real-time reservoir data exchange and coordinated drought protocols.",
                    "category": "politics",
                    "subcategory": "water_treaty",
                    "latitude": 30.04,
                    "longitude": 31.23,
                    "country": "Egypt",
                    "admin_region": "Cairo Governorate",
                    "city": "Cairo",
                    "location_confidence": 0.95,
                    "importance_score": 8.6,
                    "confidence_score": 0.89,
                    "human_impact_score": 8.8,
                    "global_impact_score": 8.5,
                    "economic_impact_score": 8.0,
                    "political_impact_score": 9.2,
                    "novelty_score": 8.5,
                    "development_velocity_score": 6.0,
                    "source_coverage_score": 8.8,
                    "first_seen_at": now - timedelta(hours=20),
                    "last_updated_at": now - timedelta(hours=4),
                    "status": "active"
                },
                "entities": [
                    {"name": "African Union", "type": "organization"},
                    {"name": "Nile Basin Initiative", "type": "organization"},
                    {"name": "Grand Ethiopian Renaissance Dam", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-aljazeera-nile-01",
                        "source_id": "src-aljazeera-en",
                        "title": "Egypt, Ethiopia, and Sudan agree on historic Nile water-sharing operational mechanism",
                        "url": "https://www.aljazeera.com/where/africa/",
                        "author": "Amina Ismail",
                        "published_at": now - timedelta(hours=20),
                        "raw_content": "After decades of diplomatic deadlock, delegations in Cairo announced agreement on binding technical guidelines for hydrological drought operation.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-france24-nile-02",
                        "source_id": "src-france24-en",
                        "title": "Cairo tripartite summit concludes with agreement on Nile reservoir management",
                        "url": "https://www.france24.com/en/africa/",
                        "author": "Marc Perelman",
                        "published_at": now - timedelta(hours=14),
                        "raw_content": "The diplomatic agreement was welcomed by international observers as a vital de-escalation of water security friction across Northeast Africa.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 7: Developing 48-Hour Cyber Outage on Air Traffic Control
            {
                "event": {
                    "id": "evt-eurocontrol-cyber-2026",
                    "canonical_title": "Coordinated Telemetry Cyberattack Disrupts Western European Air Traffic Control",
                    "summary": "Eurocontrol and national civil aviation authorities responded to a distributed service disruption across flight planning radar nodes. Contingency manual spacing protocols enacted with average 45-minute flight delays.",
                    "category": "security",
                    "subcategory": "cybersecurity",
                    "latitude": 50.85,
                    "longitude": 4.35,
                    "country": "Belgium",
                    "admin_region": "Brussels-Capital",
                    "city": "Brussels",
                    "location_confidence": 0.96,
                    "importance_score": 8.1,
                    "confidence_score": 0.90,
                    "human_impact_score": 7.2,
                    "global_impact_score": 8.0,
                    "economic_impact_score": 8.4,
                    "political_impact_score": 8.2,
                    "novelty_score": 8.6,
                    "development_velocity_score": 7.8,
                    "source_coverage_score": 8.6,
                    "first_seen_at": now - timedelta(hours=44),
                    "last_updated_at": now - timedelta(hours=2),
                    "status": "developing"
                },
                "entities": [
                    {"name": "Eurocontrol", "type": "organization"},
                    {"name": "ENISA", "type": "organization"},
                    {"name": "Brussels", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-euronews-cyber-01",
                        "source_id": "src-euronews-en",
                        "title": "European air traffic authority confirms investigation into flight plan network disruption",
                        "url": "https://www.euronews.com/travel/category/flight-delays-and-cancellations",
                        "author": "Euronews Brussels Bureau",
                        "published_at": now - timedelta(hours=44),
                        "raw_content": "Aviation agencies across Western Europe experienced intermittent network failures affecting flight route telemetry synchronization.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-dw-cyber-02",
                        "source_id": "src-dw-world",
                        "title": "Aviation cyber incident: Flights delayed across Frankfurt, Paris, and Amsterdam",
                        "url": "https://www.dw.com/en/world/s-10292",
                        "author": "Marcus Becker",
                        "published_at": now - timedelta(hours=24),
                        "raw_content": "Airlines initiated rerouting strategies as cybersecurity teams work around the clock to isolate compromised relay endpoints.",
                        "relationship_type": "update"
                    },
                    {
                        "id": "art-theguardian-cyber-03",
                        "source_id": "src-theguardian-world",
                        "title": "Air traffic systems restored to 90% capacity after unprecedented European cyber strike",
                        "url": "https://www.theguardian.com/business/aviation",
                        "author": "Dan Milmo",
                        "published_at": now - timedelta(hours=2),
                        "raw_content": "Network specialists successfully filtered the denial-of-service traffic, allowing European civil aviation to resume normal departure schedules.",
                        "relationship_type": "update"
                    }
                ]
            },

            # SCENARIO 8: Conflicting Reports on Andean Landslide Impact (Contradiction Penalty)
            {
                "event": {
                    "id": "evt-andes-landslide-2026",
                    "canonical_title": "Severe Rainstorm Triggers Destructive Debris Flow near Cusco, Southern Peru",
                    "summary": "Torrential Andean precipitation mobilized an extensive mudslide along valley roadways. State disaster agencies report 4 fatalities while local community organizers estimate over 30 individuals unaccounted for.",
                    "category": "natural_disaster",
                    "subcategory": "landslide",
                    "latitude": -13.53,
                    "longitude": -71.96,
                    "country": "Peru",
                    "admin_region": "Cusco",
                    "city": "Cusco",
                    "location_confidence": 0.88,
                    "importance_score": 7.4,
                    "confidence_score": 0.62,
                    "human_impact_score": 8.0,
                    "global_impact_score": 5.2,
                    "economic_impact_score": 6.0,
                    "political_impact_score": 5.8,
                    "novelty_score": 6.8,
                    "development_velocity_score": 6.5,
                    "source_coverage_score": 7.2,
                    "first_seen_at": now - timedelta(hours=12),
                    "last_updated_at": now - timedelta(hours=1),
                    "status": "developing"
                },
                "entities": [
                    {"name": "INDECI", "type": "organization"},
                    {"name": "Cusco Civil Defense", "type": "organization"},
                    {"name": "Urubamba Valley", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-mercopress-andes-01",
                        "source_id": "src-mercopress-en",
                        "title": "Andean mudslide cuts off provincial highway; regional authorities report 4 confirmed dead",
                        "url": "https://en.mercopress.com/peru",
                        "author": "Mercopress Lima Bureau",
                        "published_at": now - timedelta(hours=12),
                        "raw_content": "Civil defense crews in southern Peru confirmed four fatalities after torrential rain dislodged hillsides onto regional transport corridors.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-bbc-andes-02",
                        "source_id": "src-bbc-world",
                        "title": "Peru landslide: Local emergency responders fear dozens missing as rescue search continues",
                        "url": "https://www.bbc.com/news/world/latin_america",
                        "author": "Katy Watson",
                        "published_at": now - timedelta(hours=5),
                        "raw_content": "Rescue workers and municipal mayors in remote Andean hamlets disputed early casualty numbers, warning that over 30 villagers remain trapped.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 9: Mercosur - ASEAN Free Trade Agreement
            {
                "event": {
                    "id": "evt-mercosur-trade-2026",
                    "canonical_title": "Mercosur and Southeast Asian Bloc Conclude Comprehensive Free Trade Pact",
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
                "entities": [
                    {"name": "Mercosur", "type": "organization"},
                    {"name": "ASEAN", "type": "organization"},
                    {"name": "Buenos Aires", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-mercopress-trade-01",
                        "source_id": "src-mercopress-en",
                        "title": "Mercosur concludes historic commercial expansion treaty in Buenos Aires",
                        "url": "https://en.mercopress.com/mercosur",
                        "author": "Mercopress Staff",
                        "published_at": now - timedelta(hours=18),
                        "raw_content": "Foreign ministers from Brazil, Argentina, Uruguay, and Paraguay signed the final bilateral trade protocols with Southeast Asian partners today in Buenos Aires.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 10: JWST Exoplanet Atmosphere Discovery
            {
                "event": {
                    "id": "evt-jwst-exoplanet-2026",
                    "canonical_title": "James Webb Telescope Detects Stable Water Vapor Atmosphere on Rocky Exoplanet",
                    "summary": "NASA's James Webb Space Telescope confirmed the presence of a stable, non-primordial water vapor atmosphere surrounding a temperate rocky world located 40 light-years away.",
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
                "entities": [
                    {"name": "NASA", "type": "organization"},
                    {"name": "James Webb Space Telescope", "type": "concept"}
                ],
                "articles": [
                    {
                        "id": "art-ap-jwst-01",
                        "source_id": "src-ap-top",
                        "title": "NASA's Webb telescope confirms water vapor on Earth-sized rocky exoplanet",
                        "url": "https://science.nasa.gov/missions/webb/",
                        "author": "Marcia Dunn",
                        "published_at": now - timedelta(hours=14),
                        "raw_content": "Astronomers analyzing spectroscopic transmission data from NASA's Webb Space Telescope confirmed clear atmospheric signatures of water vapor on a rocky exoplanet.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 11: High North Arctic Navigation Protocols in Oslo
            {
                "event": {
                    "id": "evt-arctic-sovereignty-2026",
                    "canonical_title": "Northern States Conclude Multilateral Arctic Navigation Safety Protocol",
                    "summary": "Arctic rim nations reached a sovereign maritime consensus in Oslo governing icebreaker search-and-rescue corridors, environmental spill responses, and seasonal route access.",
                    "category": "politics",
                    "subcategory": "treaty",
                    "latitude": 59.91,
                    "longitude": 10.75,
                    "country": "Norway",
                    "admin_region": "Oslo",
                    "city": "Oslo",
                    "location_confidence": 0.98,
                    "importance_score": 7.5,
                    "confidence_score": 0.90,
                    "human_impact_score": 3.5,
                    "global_impact_score": 8.0,
                    "economic_impact_score": 7.2,
                    "political_impact_score": 8.4,
                    "novelty_score": 7.0,
                    "development_velocity_score": 4.2,
                    "source_coverage_score": 7.6,
                    "first_seen_at": now - timedelta(hours=22),
                    "last_updated_at": now - timedelta(hours=8),
                    "status": "active"
                },
                "entities": [
                    {"name": "Arctic Council", "type": "organization"},
                    {"name": "Norwegian Coast Guard", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-guardian-arctic-01",
                        "source_id": "src-theguardian-world",
                        "title": "Arctic states reach landmark deal in Oslo over northern shipping route safety",
                        "url": "https://www.theguardian.com/world/arctic",
                        "author": "Miranda Bryant",
                        "published_at": now - timedelta(hours=22),
                        "raw_content": "Diplomats from Nordic nations, Canada, and allied partners finalized coordinated rescue protocols for increasing commercial transits through Arctic passages.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 12: Singapore Global AI Governance Framework
            {
                "event": {
                    "id": "evt-singapore-ai-summit-2026",
                    "canonical_title": "Monetary Authority of Singapore Establishes Autonomous AI Risk Framework",
                    "summary": "Financial regulators in Singapore rolled out mandatory real-time audit standards and kill-switch criteria for high-frequency algorithmic agents and generative trading systems.",
                    "category": "economy",
                    "subcategory": "artificial_intelligence",
                    "latitude": 1.28,
                    "longitude": 103.85,
                    "country": "Singapore",
                    "admin_region": "Central Region",
                    "city": "Singapore",
                    "location_confidence": 0.99,
                    "importance_score": 7.3,
                    "confidence_score": 0.94,
                    "human_impact_score": 4.0,
                    "global_impact_score": 8.2,
                    "economic_impact_score": 8.6,
                    "political_impact_score": 7.0,
                    "novelty_score": 8.5,
                    "development_velocity_score": 5.2,
                    "source_coverage_score": 7.8,
                    "first_seen_at": now - timedelta(hours=26),
                    "last_updated_at": now - timedelta(hours=7),
                    "status": "active"
                },
                "entities": [
                    {"name": "Monetary Authority of Singapore", "type": "organization"},
                    {"name": "Singapore Financial Center", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-cna-singapore-01",
                        "source_id": "src-cna-asia",
                        "title": "MAS mandates algorithmic transparency and safety protocols for financial AI",
                        "url": "https://www.channelnewsasia.com/singapore",
                        "author": "Aqil Haziq Mahmud",
                        "published_at": now - timedelta(hours=26),
                        "raw_content": "Singapore's central bank introduced sweeping regulatory guidelines governing artificial intelligence models used in automated banking operations.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 13: Pan-African Solar Supergrid Initiative in Nairobi
            {
                "event": {
                    "id": "evt-kenya-green-grid-2026",
                    "canonical_title": "East African Community Unveils Multilateral Geothermal and Solar Supergrid",
                    "summary": "Development partners convened in Nairobi to launch the Great Rift Renewable Interconnector, providing cross-border HVDC power sharing between Kenya, Tanzania, and Uganda.",
                    "category": "economy",
                    "subcategory": "energy",
                    "latitude": -1.29,
                    "longitude": 36.82,
                    "country": "Kenya",
                    "admin_region": "Nairobi County",
                    "city": "Nairobi",
                    "location_confidence": 0.97,
                    "importance_score": 7.5,
                    "confidence_score": 0.89,
                    "human_impact_score": 8.2,
                    "global_impact_score": 7.4,
                    "economic_impact_score": 8.0,
                    "political_impact_score": 7.2,
                    "novelty_score": 7.2,
                    "development_velocity_score": 4.8,
                    "source_coverage_score": 7.5,
                    "first_seen_at": now - timedelta(hours=30),
                    "last_updated_at": now - timedelta(hours=10),
                    "status": "active"
                },
                "entities": [
                    {"name": "East African Community", "type": "organization"},
                    {"name": "African Development Bank", "type": "organization"},
                    {"name": "Nairobi", "type": "location"}
                ],
                "articles": [
                    {
                        "id": "art-france24-kenya-01",
                        "source_id": "src-france24-en",
                        "title": "Nairobi summit launches multi-country clean power transmission network",
                        "url": "https://www.france24.com/en/tag/energy/",
                        "author": "Nicholas Norbrook",
                        "published_at": now - timedelta(hours=30),
                        "raw_content": "Regional leaders in Kenya broke ground on the continent's largest synchronous clean power grid project.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 14: Baltic Underwater Power Cable Anomaly
            {
                "event": {
                    "id": "evt-baltic-grid-2026",
                    "canonical_title": "Investigation Opened into Power Grid Telemetry Anomaly in Eastern Baltic",
                    "summary": "Regional transmission operators reported unexpected high-voltage oscillations along subsea electrical interconnectors. Initial speculation of physical tampering remains unconfirmed.",
                    "category": "security",
                    "subcategory": "infrastructure",
                    "latitude": 56.95,
                    "longitude": 24.1,
                    "country": "Latvia",
                    "admin_region": "Vidzeme",
                    "city": "Riga",
                    "location_confidence": 0.70,
                    "importance_score": 6.8,
                    "confidence_score": 0.45,
                    "human_impact_score": 5.0,
                    "global_impact_score": 6.5,
                    "economic_impact_score": 6.2,
                    "political_impact_score": 7.4,
                    "novelty_score": 8.0,
                    "development_velocity_score": 6.0,
                    "source_coverage_score": 5.5,
                    "first_seen_at": now - timedelta(hours=14),
                    "last_updated_at": now - timedelta(hours=3),
                    "status": "developing"
                },
                "entities": [
                    {"name": "Augstsprieguma tikls", "type": "organization"},
                    {"name": "Baltic Sea Maritime Command", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-euronews-baltic-01",
                        "source_id": "src-euronews-en",
                        "title": "Baltic grid operators investigate electrical fluctuations; sabotage unconfirmed",
                        "url": "https://www.euronews.com/business/energy",
                        "author": "Euronews Riga Bureau",
                        "published_at": now - timedelta(hours=14),
                        "raw_content": "Transmission system operators in the Baltic region are investigating unusual telemetry spikes. Officials caution against jumping to conclusions.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 15: Global Central Bank Policy Divergence in Washington
            {
                "event": {
                    "id": "evt-fed-ecb-divergence-2026",
                    "canonical_title": "Federal Reserve and Global Central Banks Signal Divergent Monetary Trajectories",
                    "summary": "At the annual monetary symposium, central bankers outlined diverging policy paths as consumer prices normalize in Europe while North American productivity benchmarks drive sustained capital investment.",
                    "category": "economy",
                    "subcategory": "monetary_policy",
                    "latitude": 38.89,
                    "longitude": -77.04,
                    "country": "United States",
                    "admin_region": "District of Columbia",
                    "city": "Washington",
                    "location_confidence": 0.99,
                    "importance_score": 7.8,
                    "confidence_score": 0.95,
                    "human_impact_score": 5.5,
                    "global_impact_score": 8.8,
                    "economic_impact_score": 9.4,
                    "political_impact_score": 7.2,
                    "novelty_score": 6.8,
                    "development_velocity_score": 5.4,
                    "source_coverage_score": 9.0,
                    "first_seen_at": now - timedelta(hours=12),
                    "last_updated_at": now - timedelta(hours=2),
                    "status": "active"
                },
                "entities": [
                    {"name": "Federal Reserve", "type": "organization"},
                    {"name": "European Central Bank", "type": "organization"},
                    {"name": "International Monetary Fund", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-reuters-fed-01",
                        "source_id": "src-reuters-world",
                        "title": "Central bank chiefs articulate diverging interest rate paths amid shifting trade currents",
                        "url": "https://www.reuters.com/markets/us/",
                        "author": "Howard Schneider",
                        "published_at": now - timedelta(hours=12),
                        "raw_content": "Monetary authorities from the United States, Europe, and Asia emphasized differing domestic inflation fundamentals during opening plenary remarks.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 16: South Asia - Bay of Bengal Climate & Coastal Resilience Accord (Dhaka, Bangladesh)
            {
                "event": {
                    "id": "evt-south-asia-monsoon-2026",
                    "canonical_title": "South Asian Coastal Defense & Monsoon Early Warning Accord Inked in Dhaka",
                    "summary": "Environmental ministers from Bangladesh, India, and Sri Lanka ratified a historic joint disaster-mitigation framework in Dhaka, deploying shared tidal radars, sea wall fortification standards, and real-time storm data synchronization across the Bay of Bengal.",
                    "category": "environment",
                    "subcategory": "climate_resilience",
                    "latitude": 23.81,
                    "longitude": 90.41,
                    "country": "Bangladesh",
                    "admin_region": "Dhaka",
                    "city": "Dhaka",
                    "location_confidence": 0.98,
                    "importance_score": 8.1,
                    "confidence_score": 0.94,
                    "human_impact_score": 8.6,
                    "global_impact_score": 7.4,
                    "economic_impact_score": 7.8,
                    "political_impact_score": 8.0,
                    "novelty_score": 7.9,
                    "development_velocity_score": 7.2,
                    "source_coverage_score": 8.8,
                    "first_seen_at": now - timedelta(hours=6),
                    "last_updated_at": now - timedelta(hours=1),
                    "status": "active"
                },
                "entities": [
                    {"name": "Bangladesh Meteorological Department", "type": "organization"},
                    {"name": "India Meteorological Department", "type": "organization"},
                    {"name": "Bay of Bengal Initiative", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-dailystar-monsoon-01",
                        "source_id": "src-dailystar-bd",
                        "title": "South Asian littoral nations sign landmark Bay of Bengal storm resilience pact in Dhaka",
                        "url": "https://www.thedailystar.net/frontpage/",
                        "author": "Rezaul Karim",
                        "published_at": now - timedelta(hours=6),
                        "raw_content": "A high-level climate adaptation treaty was ratified in Dhaka today, establishing a synchronized coastal radar net and multi-nation storm response teams.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-thehindu-monsoon-02",
                        "source_id": "src-thehindu-in",
                        "title": "India and regional partners activate unified maritime cyclone telemetry grid",
                        "url": "https://www.thehindu.com/news/national/",
                        "author": "Sujatha Prasad",
                        "published_at": now - timedelta(hours=4, minutes=30),
                        "raw_content": "Meteorological authorities confirmed integration of Chennai and Chittagong Doppler radar feeds into the unified regional early warning network.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 17: Southeast Asia - Pan-ASEAN High-Speed Transit Corridor (Bangkok, Thailand)
            {
                "event": {
                    "id": "evt-asean-rail-corridor-2026",
                    "canonical_title": "ASEAN Finalizes High-Speed Transit Corridor Linking Bangkok, Kuala Lumpur, and Singapore",
                    "summary": "Transport ministers gathered at the Bangkok Grand Central Terminal to finalize the interoperability protocol for the unified Pan-ASEAN electrified high-speed rail corridor, slating direct transit from Bangkok to Singapore within seven hours.",
                    "category": "economy",
                    "subcategory": "infrastructure",
                    "latitude": 13.75,
                    "longitude": 100.50,
                    "country": "Thailand",
                    "admin_region": "Bangkok",
                    "city": "Bangkok",
                    "location_confidence": 0.99,
                    "importance_score": 8.0,
                    "confidence_score": 0.93,
                    "human_impact_score": 7.6,
                    "global_impact_score": 7.9,
                    "economic_impact_score": 9.1,
                    "political_impact_score": 7.8,
                    "novelty_score": 8.3,
                    "development_velocity_score": 6.8,
                    "source_coverage_score": 8.9,
                    "first_seen_at": now - timedelta(hours=9),
                    "last_updated_at": now - timedelta(hours=2),
                    "status": "active"
                },
                "entities": [
                    {"name": "State Railway of Thailand", "type": "organization"},
                    {"name": "Keretapi Tanah Melayu", "type": "organization"},
                    {"name": "ASEAN Transport Secretariat", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-bangkokpost-rail-01",
                        "source_id": "src-bangkokpost-th",
                        "title": "Bangkok transit summit approves unified standard gauge for Pan-ASEAN rail link",
                        "url": "https://www.bangkokpost.com/business/",
                        "author": "Somchai Nimit",
                        "published_at": now - timedelta(hours=9),
                        "raw_content": "Transport chiefs from Thailand, Malaysia, and Singapore signed a historic tripartite agreement synchronizing signals and customs for the high-speed line.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-straitstimes-rail-02",
                        "source_id": "src-straitstimes-sg",
                        "title": "Seamless cross-border express trains move closer as Bangkok-Singapore rail accord clears",
                        "url": "https://www.straitstimes.com/asia/se-asia",
                        "author": "Tan Boon Seng",
                        "published_at": now - timedelta(hours=7),
                        "raw_content": "The unified rail corridor is expected to slash logistics costs and aviation emissions across Southeast Asia once passenger trials commence.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 18: Middle East - World's Largest Solar Desalination Array (Riyadh, Saudi Arabia)
            {
                "event": {
                    "id": "evt-gulf-green-hydrogen-2026",
                    "canonical_title": "Saudi Arabia and UAE Inaugurate World's Largest Solar Desalination Complex",
                    "summary": "Officials in Riyadh cut the ribbon on a 4.5 GW solar-powered reverse osmosis seawater desalination facility capable of generating 1.2 million cubic meters of potable water daily, setting a benchmark for water security across arid regions.",
                    "category": "science_technology",
                    "subcategory": "clean_energy",
                    "latitude": 24.71,
                    "longitude": 46.67,
                    "country": "Saudi Arabia",
                    "admin_region": "Riyadh",
                    "city": "Riyadh",
                    "location_confidence": 0.99,
                    "importance_score": 8.2,
                    "confidence_score": 0.95,
                    "human_impact_score": 8.7,
                    "global_impact_score": 8.2,
                    "economic_impact_score": 8.6,
                    "political_impact_score": 7.4,
                    "novelty_score": 8.4,
                    "development_velocity_score": 6.5,
                    "source_coverage_score": 8.7,
                    "first_seen_at": now - timedelta(hours=8),
                    "last_updated_at": now - timedelta(hours=1, minutes=45),
                    "status": "active"
                },
                "entities": [
                    {"name": "Saline Water Conversion Corporation", "type": "organization"},
                    {"name": "ACWA Power", "type": "organization"},
                    {"name": "Masdar Clean Energy", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-arabnews-solar-01",
                        "source_id": "src-arabnews-sa",
                        "title": "Riyadh unveils state-of-the-art solar water desalination plant powering 3 million residents",
                        "url": "https://www.arabnews.com/saudi-arabia",
                        "author": "Tariq Al-Harbi",
                        "published_at": now - timedelta(hours=8),
                        "raw_content": "The zero-carbon facility leverages high-efficiency photovoltaic cells to power ultra-filtration membranes, dramatically lowering municipal energy footprints.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-thenational-solar-02",
                        "source_id": "src-thenational-ae",
                        "title": "Gulf clean water transition accelerates as Riyadh mega-desalination project begins operations",
                        "url": "https://www.thenationalnews.com/business/energy/",
                        "author": "Nadia Salem",
                        "published_at": now - timedelta(hours=6, minutes=15),
                        "raw_content": "Regional energy ministers lauded the facility as a blueprint for drought-prone nations globally seeking fossil-free municipal water independence.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 19: Sub-Saharan Africa - Silicon Savannah Instant Payment Grid (Nairobi, Kenya)
            {
                "event": {
                    "id": "evt-africa-silicon-savannah-2026",
                    "canonical_title": "Pan-African Instant Cross-Border Payment System Launched in Nairobi",
                    "summary": "Central bank governors from Kenya, Nigeria, South Africa, and Ghana unveiled a unified mobile settlement switch in Nairobi, eliminating foreign currency intermediaries for trade across 24 African economies.",
                    "category": "economy",
                    "subcategory": "fintech",
                    "latitude": -1.29,
                    "longitude": 36.82,
                    "country": "Kenya",
                    "admin_region": "Nairobi",
                    "city": "Nairobi",
                    "location_confidence": 0.98,
                    "importance_score": 8.0,
                    "confidence_score": 0.94,
                    "human_impact_score": 8.4,
                    "global_impact_score": 8.0,
                    "economic_impact_score": 9.2,
                    "political_impact_score": 7.7,
                    "novelty_score": 8.5,
                    "development_velocity_score": 7.0,
                    "source_coverage_score": 8.9,
                    "first_seen_at": now - timedelta(hours=10),
                    "last_updated_at": now - timedelta(hours=2),
                    "status": "active"
                },
                "entities": [
                    {"name": "Central Bank of Kenya", "type": "organization"},
                    {"name": "African Continental Free Trade Area", "type": "organization"},
                    {"name": "PAPSS Payment Network", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-dailynation-fintech-01",
                        "source_id": "src-dailynation-ke",
                        "title": "Nairobi launches cross-border digital shilling and intra-Africa instant settlement network",
                        "url": "https://nation.africa/kenya/business",
                        "author": "Mwangi Gikonyo",
                        "published_at": now - timedelta(hours=10),
                        "raw_content": "Small traders and businesses can now send payments directly in local currencies within seconds across East and West Africa without routing through overseas dollars.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-theeastafrican-fintech-02",
                        "source_id": "src-theeastafrican-ke",
                        "title": "African trade gets digital boost as intra-continental payment switch goes live",
                        "url": "https://www.theeastafrican.co.ke/tea/business",
                        "author": "Alice Mutua",
                        "published_at": now - timedelta(hours=7, minutes=30),
                        "raw_content": "Economists predict transaction fee reductions of up to 80% for cross-border commerce as mobile payment interoperability takes effect.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 20: Latin America - Amazon Biodiversity Protection & Satellite Monitoring Compact (São Paulo, Brazil)
            {
                "event": {
                    "id": "evt-amazon-bioeconomy-pact-2026",
                    "canonical_title": "Brazil and Colombia Launch Joint Satellite Monitoring Task Force to Safeguard Amazon Basin",
                    "summary": "Environmental agencies from Brazil, Colombia, and Peru established a joint aerospace command in São Paulo utilizing synthetic aperture radar to detect unauthorized deforestation and protect indigenous reserve boundaries in real time.",
                    "category": "environment",
                    "subcategory": "conservation",
                    "latitude": -23.55,
                    "longitude": -46.63,
                    "country": "Brazil",
                    "admin_region": "Sao Paulo",
                    "city": "Sao Paulo",
                    "location_confidence": 0.98,
                    "importance_score": 8.3,
                    "confidence_score": 0.94,
                    "human_impact_score": 8.2,
                    "global_impact_score": 8.9,
                    "economic_impact_score": 7.3,
                    "political_impact_score": 8.1,
                    "novelty_score": 8.0,
                    "development_velocity_score": 6.8,
                    "source_coverage_score": 8.7,
                    "first_seen_at": now - timedelta(hours=11),
                    "last_updated_at": now - timedelta(hours=3),
                    "status": "active"
                },
                "entities": [
                    {"name": "INPE Space Agency", "type": "organization"},
                    {"name": "IBAMA Environmental Enforcement", "type": "organization"},
                    {"name": "Amazon Conservation Treaty Organization", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-riotimes-amazon-01",
                        "source_id": "src-riotimes-br",
                        "title": "Brazil, Colombia launch coordinated radar constellation to patrol Amazon rainforest canopy",
                        "url": "https://riotimesonline.com/brazil-news/",
                        "author": "Gabriela Silva",
                        "published_at": now - timedelta(hours=11),
                        "raw_content": "The cloud-piercing radar network provides continuous day-and-night surveillance over dense rainforest canopies, triggering immediate ranger dispatches upon disturbance.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-bogotapost-amazon-02",
                        "source_id": "src-bogotapost-co",
                        "title": "Cross-border environmental enforcement unites Andean and Amazonian nations",
                        "url": "https://thebogotapost.com/",
                        "author": "Camilo Restrepo",
                        "published_at": now - timedelta(hours=8),
                        "raw_content": "Colombian environment officials highlighted the critical importance of coordinated telemetry to halt illicit logging networks operating along border rivers.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 21: Eastern & Northern Europe - Baltic Offshore Wind Supergrid Interconnection (Gdansk, Poland)
            {
                "event": {
                    "id": "evt-baltic-wind-supergrid-2026",
                    "canonical_title": "Poland and Baltic States Commission 3.2 GW Offshore Wind Supergrid Array",
                    "summary": "Energy ministers from Poland, Lithuania, and Latvia gathered in Gdansk to inaugurate the Baltic offshore HVDC interconnection hub, linking 3.2 gigawatts of deepwater wind generation into the unified European transmission grid.",
                    "category": "economy",
                    "subcategory": "energy_security",
                    "latitude": 54.35,
                    "longitude": 18.64,
                    "country": "Poland",
                    "admin_region": "Pomerania",
                    "city": "Gdansk",
                    "location_confidence": 0.98,
                    "importance_score": 7.9,
                    "confidence_score": 0.93,
                    "human_impact_score": 7.1,
                    "global_impact_score": 8.1,
                    "economic_impact_score": 8.7,
                    "political_impact_score": 8.2,
                    "novelty_score": 7.8,
                    "development_velocity_score": 6.4,
                    "source_coverage_score": 8.6,
                    "first_seen_at": now - timedelta(hours=13),
                    "last_updated_at": now - timedelta(hours=4),
                    "status": "active"
                },
                "entities": [
                    {"name": "PGE Polska Grupa Energetyczna", "type": "organization"},
                    {"name": "Litgrid", "type": "organization"},
                    {"name": "Baltic Offshore Wind Initiative", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-notesfrompoland-wind-01",
                        "source_id": "src-notesfrompoland-pl",
                        "title": "Poland connects massive Baltic offshore wind cluster to national power network",
                        "url": "https://notesfrompoland.com/",
                        "author": "Mateusz Wozniak",
                        "published_at": now - timedelta(hours=13),
                        "raw_content": "The offshore substation off Gdansk marks Poland's single largest renewable power asset, displacing over 4 million tons of coal emissions annually.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-baltictimes-wind-02",
                        "source_id": "src-baltictimes-lv",
                        "title": "Baltic states celebrate milestone in regional energy independence with offshore grid launch",
                        "url": "https://www.baltictimes.com/news/",
                        "author": "Janis Berzins",
                        "published_at": now - timedelta(hours=10),
                        "raw_content": "The synchronized HVDC link solidifies the complete desynchronization of the Baltic power network from legacy eastern grids.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 22: Oceania & Pacific Islands - Ocean Buoy Sensor Grid for Tsunami Tracking (Suva, Fiji)
            {
                "event": {
                    "id": "evt-pacific-early-warning-2026",
                    "canonical_title": "Pacific Islands Forum Deploys Deep-Ocean Acoustic Sensor Grid for Real-Time Tsunami Tracking",
                    "summary": "Representatives from Fiji, Samoa, Tonga, and New Zealand activated an expansive deep-ocean DART buoy array centered in Suva, delivering sub-minute seismic shock wave detection and coastal storm surge predictions across the South Pacific.",
                    "category": "science_technology",
                    "subcategory": "disaster_prevention",
                    "latitude": -18.14,
                    "longitude": 178.44,
                    "country": "Fiji",
                    "admin_region": "Central",
                    "city": "Suva",
                    "location_confidence": 0.97,
                    "importance_score": 7.8,
                    "confidence_score": 0.92,
                    "human_impact_score": 8.5,
                    "global_impact_score": 7.2,
                    "economic_impact_score": 6.8,
                    "political_impact_score": 7.0,
                    "novelty_score": 8.1,
                    "development_velocity_score": 7.4,
                    "source_coverage_score": 8.4,
                    "first_seen_at": now - timedelta(hours=15),
                    "last_updated_at": now - timedelta(hours=5),
                    "status": "active"
                },
                "entities": [
                    {"name": "Pacific Community (SPC)", "type": "organization"},
                    {"name": "Fiji Mineral Resources Department", "type": "organization"},
                    {"name": "GNS Science New Zealand", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-islandsbusiness-tsunami-01",
                        "source_id": "src-islandsbusiness-fj",
                        "title": "Pacific nations unveil multi-million-dollar deep ocean tsunami sensor shield in Suva",
                        "url": "https://islandsbusiness.com/",
                        "author": "Vilimoni Bainimarama",
                        "published_at": now - timedelta(hours=15),
                        "raw_content": "Deep seafloor pressure sensors linked via acoustic modems will give vulnerable coastal atolls vital evacuation warnings before tidal crests hit shores.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-rnz-tsunami-02",
                        "source_id": "src-rnz-nz",
                        "title": "NZ scientists collaborate with Pacific neighbours to deploy real-time seabed warning network",
                        "url": "https://www.rnz.co.nz/international/pacific-news",
                        "author": "Moana Ellis",
                        "published_at": now - timedelta(hours=12),
                        "raw_content": "Wellington and Pacific island governments confirmed the first batch of operational telemetry was successfully received at regional hazard centers.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 23: Caribbean - Island Solar Microgrid Resilience Architecture (Kingston, Jamaica)
            {
                "event": {
                    "id": "evt-caribbean-microgrid-2026",
                    "canonical_title": "CARICOM Unveils Hurricane-Resilient Island Solar Microgrid Grid Architecture",
                    "summary": "Caribbean energy authorities convened in Kingston to launch a 350 MW distributed solar and battery storage architecture engineered to withstand Category 5 wind speeds, ensuring hospital and emergency communication uptime during tropical cyclones.",
                    "category": "environment",
                    "subcategory": "resilience",
                    "latitude": 17.97,
                    "longitude": -76.79,
                    "country": "Jamaica",
                    "admin_region": "Surrey",
                    "city": "Kingston",
                    "location_confidence": 0.98,
                    "importance_score": 7.7,
                    "confidence_score": 0.92,
                    "human_impact_score": 8.3,
                    "global_impact_score": 7.0,
                    "economic_impact_score": 7.6,
                    "political_impact_score": 7.2,
                    "novelty_score": 8.2,
                    "development_velocity_score": 6.7,
                    "source_coverage_score": 8.3,
                    "first_seen_at": now - timedelta(hours=14),
                    "last_updated_at": now - timedelta(hours=3, minutes=30),
                    "status": "active"
                },
                "entities": [
                    {"name": "CARICOM Energy Directorate", "type": "organization"},
                    {"name": "Jamaica Public Service Company", "type": "organization"},
                    {"name": "Caribbean Development Bank", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-jamaicagleaner-microgrid-01",
                        "source_id": "src-jamaicagleaner-jm",
                        "title": "Jamaica and CARICOM roll out hardened solar microgrids to bulletproof critical utilities",
                        "url": "https://jamaica-gleaner.com/",
                        "author": "Althea Crawford",
                        "published_at": now - timedelta(hours=14),
                        "raw_content": "Engineered with reinforced aerodynamic tracking mounts and subterranean battery vaults, the microgrid nodes are built to resist extreme hurricane gusts.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 24: Kazakhstan - Trans-Caspian Middle Corridor Rail Electrification (Astana, Kazakhstan)
            {
                "event": {
                    "id": "evt-trans-caspian-middle-corridor-2026",
                    "canonical_title": "Trans-Caspian Middle Corridor Rail Electrification Pact Inked in Astana",
                    "summary": "Kazakhstan, Azerbaijan, and Georgia finalized a joint investment pact in Astana to electrify 1,400 km of freight railways and expand container terminal capacity at Aktau and Kuryk ports, doubling Trans-Caspian trade throughput between Asia and Europe.",
                    "category": "economy",
                    "subcategory": "transport_corridor",
                    "latitude": 51.17,
                    "longitude": 71.45,
                    "country": "Kazakhstan",
                    "admin_region": "Akmola",
                    "city": "Astana",
                    "location_confidence": 0.99,
                    "importance_score": 8.4,
                    "confidence_score": 0.95,
                    "human_impact_score": 7.5,
                    "global_impact_score": 8.5,
                    "economic_impact_score": 9.4,
                    "political_impact_score": 8.0,
                    "novelty_score": 8.2,
                    "development_velocity_score": 7.1,
                    "source_coverage_score": 8.8,
                    "first_seen_at": now - timedelta(hours=5),
                    "last_updated_at": now - timedelta(hours=1),
                    "status": "active"
                },
                "entities": [
                    {"name": "Kazakhstan Temir Zholy (KTZ)", "type": "organization"},
                    {"name": "Middle Corridor Association", "type": "organization"},
                    {"name": "Port of Aktau Authority", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-astanatimes-corridor-01",
                        "source_id": "src-astanatimes-kz",
                        "title": "Astana signs landmark agreement to double Trans-Caspian cargo rail throughput",
                        "url": "https://astanatimes.com/middle-corridor-rail-electrification",
                        "author": "Aigerim Seisembayeva",
                        "published_at": now - timedelta(hours=5),
                        "raw_content": "The Middle Corridor transport alliance ratified plans to deploy computerized block signaling and rapid container cranes across Caspian ferry docks.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-eurasianet-corridor-02",
                        "source_id": "src-eurasianet-regional",
                        "title": "Central Asia accelerates bypass routes as Trans-Caspian cargo volumes surge",
                        "url": "https://eurasianet.org/central-asia-trans-caspian-rail",
                        "author": "Almaz Kumenov",
                        "published_at": now - timedelta(hours=3, minutes=30),
                        "raw_content": "Freight operators reported average transit times between China border dry ports and European hubs fell to under 12 days following initial electrification.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 25: Uzbekistan - Transboundary Aral Sea & River Water Sharing Accord (Tashkent, Uzbekistan)
            {
                "event": {
                    "id": "evt-central-asia-water-pact-2026",
                    "canonical_title": "Central Asian Republics Ratify Syr Darya & Amu Darya Transboundary Water Sharing Accord in Tashkent",
                    "summary": "Ministers of water resources from Uzbekistan, Kazakhstan, Kyrgyzstan, and Tajikistan signed an automated telemetry monitoring protocol in Tashkent, establishing algorithmic seasonal flow quotas and unified reservoir release schedules to prevent regional drought and mitigate Aral Sea soil salinity.",
                    "category": "environment",
                    "subcategory": "water_security",
                    "latitude": 41.30,
                    "longitude": 69.24,
                    "country": "Uzbekistan",
                    "admin_region": "Tashkent",
                    "city": "Tashkent",
                    "location_confidence": 0.99,
                    "importance_score": 8.3,
                    "confidence_score": 0.94,
                    "human_impact_score": 8.8,
                    "global_impact_score": 7.8,
                    "economic_impact_score": 8.4,
                    "political_impact_score": 8.2,
                    "novelty_score": 8.0,
                    "development_velocity_score": 6.9,
                    "source_coverage_score": 8.6,
                    "first_seen_at": now - timedelta(hours=7),
                    "last_updated_at": now - timedelta(hours=2),
                    "status": "active"
                },
                "entities": [
                    {"name": "Interstate Commission for Water Coordination", "type": "organization"},
                    {"name": "Uzbekistan Ministry of Water Resources", "type": "organization"},
                    {"name": "International Fund for Saving the Aral Sea", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-timesca-water-01",
                        "source_id": "src-timesca-centralasia",
                        "title": "Central Asian nations reach historic automated water allocation pact in Tashkent",
                        "url": "https://timesca.com/central-asia-water-pact-tashkent",
                        "author": "Rustam Mirzaev",
                        "published_at": now - timedelta(hours=7),
                        "raw_content": "Smart river flow sensor arrays along the Syr Darya and Amu Darya will provide real-time public telemetry to eliminate allocation disputes among upstream and downstream nations.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-uzdaily-water-02",
                        "source_id": "src-uzdaily-uz",
                        "title": "Tashkent summit implements algorithmic reservoir coordination to safeguard agrarian harvest",
                        "url": "https://www.uzdaily.uz/en/central-asia-water-sharing-accord",
                        "author": "Dilshod Karimov",
                        "published_at": now - timedelta(hours=4),
                        "raw_content": "The agreement incorporates remote sensing imagery from EU Copernicus satellites to audit soil moisture and minimize irrigation loss.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 26: Azerbaijan & Caspian Sea - 1,100 km Subsea Renewable Power Cable (Baku, Azerbaijan)
            {
                "event": {
                    "id": "evt-caspian-green-energy-cable-2026",
                    "canonical_title": "Baku Inaugurates 1,100 km Subsea Caspian Renewable Power Cable Project",
                    "summary": "Energy executives and state delegates gathered at the Baku Maritime Terminal to commence laying a high-voltage direct current (HVDC) subsea power line under the Caspian Sea, connecting western Kazakhstan's wind fields to the South Caucasus transmission grid.",
                    "category": "science_technology",
                    "subcategory": "clean_energy",
                    "latitude": 40.41,
                    "longitude": 49.87,
                    "country": "Azerbaijan",
                    "admin_region": "Absheron",
                    "city": "Baku",
                    "location_confidence": 0.98,
                    "importance_score": 8.1,
                    "confidence_score": 0.93,
                    "human_impact_score": 7.3,
                    "global_impact_score": 8.3,
                    "economic_impact_score": 8.9,
                    "political_impact_score": 7.9,
                    "novelty_score": 8.3,
                    "development_velocity_score": 6.8,
                    "source_coverage_score": 8.5,
                    "first_seen_at": now - timedelta(hours=9),
                    "last_updated_at": now - timedelta(hours=2, minutes=30),
                    "status": "active"
                },
                "entities": [
                    {"name": "Azerenerji", "type": "organization"},
                    {"name": "Samruk-Energy", "type": "organization"},
                    {"name": "Caspian Subsea Energy Grid", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-azernews-cable-01",
                        "source_id": "src-azernews-az",
                        "title": "Baku begins cable-laying operations for landmark trans-Caspian green energy artery",
                        "url": "https://www.azernews.az/energy/caspian-green-power-cable",
                        "author": "Farid Mammadov",
                        "published_at": now - timedelta(hours=9),
                        "raw_content": "The 2-gigawatt underwater transmission link will transmit clean steppe wind energy across the Caspian Sea directly into regional interconnections.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-eurasianet-cable-02",
                        "source_id": "src-eurasianet-regional",
                        "title": "Caspian states unite around subsea electricity highway linking Central Asia and Caucasus",
                        "url": "https://eurasianet.org/azerbaijan-caspian-subsea-power-cable",
                        "author": "Nurlan Aliyev",
                        "published_at": now - timedelta(hours=6),
                        "raw_content": "The ambitious subsea infrastructure cements the Caspian basin as an emerging exporter of zero-emission electricity.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 27: Kyrgyzstan & Tajikistan - Tian Shan Alpine Glacier Preservation Network (Bishkek, Kyrgyzstan)
            {
                "event": {
                    "id": "evt-tian-shan-glacier-preservation-2026",
                    "canonical_title": "Tian Shan Glacier Preservation & Alpine Hydroelectric Network Deployed Across Bishkek and Dushanbe",
                    "summary": "Glaciologists and power grid operators in Bishkek deployed a 40-station laser-ranging radar network across the Tian Shan mountain range to forecast glacial melt runoff and optimize peak hydropower generation for the Central Asian energy ring.",
                    "category": "environment",
                    "subcategory": "glaciology",
                    "latitude": 42.87,
                    "longitude": 74.59,
                    "country": "Kyrgyzstan",
                    "admin_region": "Chuy",
                    "city": "Bishkek",
                    "location_confidence": 0.98,
                    "importance_score": 7.9,
                    "confidence_score": 0.92,
                    "human_impact_score": 8.1,
                    "global_impact_score": 7.6,
                    "economic_impact_score": 7.7,
                    "political_impact_score": 7.2,
                    "novelty_score": 8.1,
                    "development_velocity_score": 6.5,
                    "source_coverage_score": 8.3,
                    "first_seen_at": now - timedelta(hours=11),
                    "last_updated_at": now - timedelta(hours=3),
                    "status": "active"
                },
                "entities": [
                    {"name": "Central Asian Institute for Applied Geosciences", "type": "organization"},
                    {"name": "Kyrgyz National Academy of Sciences", "type": "organization"},
                    {"name": "Toktogul Hydropower Cascade", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-timesca-glacier-01",
                        "source_id": "src-timesca-centralasia",
                        "title": "Bishkek deploys high-altitude radar network to monitor Tian Shan glacier stability",
                        "url": "https://timesca.com/tian-shan-glacier-preservation-network",
                        "author": "Bakyt Asanov",
                        "published_at": now - timedelta(hours=11),
                        "raw_content": "Solar-powered alpine telemetry stations anchored at 4,000 meters elevation stream real-time snowpack depth and melt velocity data to flood-control authorities.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 28: Georgia & Caucasus - Black Sea High-Bandwidth Terabit Fiber Link (Tbilisi, Georgia)
            {
                "event": {
                    "id": "evt-caucasus-digital-arterial-2026",
                    "canonical_title": "Georgia and Black Sea Partners Complete High-Bandwidth Subsea Terabit Fiber Link in Tbilisi",
                    "summary": "Telecommunication consortiums in Tbilisi and Batumi activated the Black Sea Terabit Submarine Cable, establishing a fault-tolerant ultra-low-latency digital bridge connecting Central Asian data centers to European internet exchange hubs in Frankfurt and Sofia.",
                    "category": "science_technology",
                    "subcategory": "telecommunications",
                    "latitude": 41.72,
                    "longitude": 44.78,
                    "country": "Georgia",
                    "admin_region": "Tbilisi",
                    "city": "Tbilisi",
                    "location_confidence": 0.98,
                    "importance_score": 7.8,
                    "confidence_score": 0.93,
                    "human_impact_score": 6.8,
                    "global_impact_score": 8.0,
                    "economic_impact_score": 8.6,
                    "political_impact_score": 7.7,
                    "novelty_score": 8.0,
                    "development_velocity_score": 6.2,
                    "source_coverage_score": 8.4,
                    "first_seen_at": now - timedelta(hours=13),
                    "last_updated_at": now - timedelta(hours=4),
                    "status": "active"
                },
                "entities": [
                    {"name": "Georgian National Communications Commission", "type": "organization"},
                    {"name": "Black Sea Subsea Cable Consortium", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-agenda-fiber-01",
                        "source_id": "src-agenda-ge",
                        "title": "Tbilisi celebrates activation of Black Sea submarine fiber cable connecting Caucasus to Europe",
                        "url": "https://agenda.ge/en/black-sea-submarine-fiber-cable",
                        "author": "Nino Kalandadze",
                        "published_at": now - timedelta(hours=13),
                        "raw_content": "The 1,200 km deep-water optical fiber line secures digital sovereignty and redundant internet connectivity for millions across the South Caucasus and Central Asia.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 29: Turkmenistan - Trans-Caspian Methane Abatement & Infrastructure Framework (Ashgabat, Turkmenistan)
            {
                "event": {
                    "id": "evt-trans-caspian-gas-interconnect-2026",
                    "canonical_title": "Ashgabat Greenlights Methane Abatement & Caspian Infrastructure Modernization Framework",
                    "summary": "Turkmen energy authorities in Ashgabat ratified a $1.8B environmental transition roadmap installing zero-emission vapor-recovery compressors across the Galkynysh and Caspian offshore fields to capture flare gas and feed regional distribution grids.",
                    "category": "economy",
                    "subcategory": "energy_transition",
                    "latitude": 37.96,
                    "longitude": 58.33,
                    "country": "Turkmenistan",
                    "admin_region": "Ahal",
                    "city": "Ashgabat",
                    "location_confidence": 0.97,
                    "importance_score": 7.7,
                    "confidence_score": 0.91,
                    "human_impact_score": 7.2,
                    "global_impact_score": 7.9,
                    "economic_impact_score": 8.3,
                    "political_impact_score": 7.5,
                    "novelty_score": 7.8,
                    "development_velocity_score": 6.0,
                    "source_coverage_score": 8.2,
                    "first_seen_at": now - timedelta(hours=14),
                    "last_updated_at": now - timedelta(hours=4, minutes=30),
                    "status": "active"
                },
                "entities": [
                    {"name": "Turkmengaz", "type": "organization"},
                    {"name": "Caspian Environmental Protection Council", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-timesca-methane-01",
                        "source_id": "src-timesca-centralasia",
                        "title": "Turkmenistan launches sweeping methane capture overhaul across Caspian energy fields",
                        "url": "https://timesca.com/turkmenistan-methane-abatement-caspian",
                        "author": "Myrat Orazov",
                        "published_at": now - timedelta(hours=14),
                        "raw_content": "The modernization program eliminates legacy flaring stacks, routing re-compressed natural gas into regional domestic heating grids.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 30: Turkey & Black Sea - Maritime Radar Net Modernization (Istanbul, Turkey)
            {
                "event": {
                    "id": "evt-blacksea-maritime-surveillance-2026",
                    "canonical_title": "Turkey and Black Sea Littoral Command Expand Automated Maritime Radar Net",
                    "summary": "Turkish coast guard and port authorities in Istanbul integrated synthetic aperture coastal radar domes across the Bosphorus Strait and Black Sea maritime zones, providing 24/7 autonomous vessel tracking and uncrewed drone collision avoidance.",
                    "category": "security_defense",
                    "subcategory": "maritime_security",
                    "latitude": 41.00,
                    "longitude": 28.97,
                    "country": "Turkey",
                    "admin_region": "Marmara",
                    "city": "Istanbul",
                    "location_confidence": 0.99,
                    "importance_score": 8.0,
                    "confidence_score": 0.94,
                    "human_impact_score": 7.4,
                    "global_impact_score": 8.2,
                    "economic_impact_score": 8.6,
                    "political_impact_score": 8.1,
                    "novelty_score": 8.0,
                    "development_velocity_score": 7.0,
                    "source_coverage_score": 8.7,
                    "first_seen_at": now - timedelta(hours=10),
                    "last_updated_at": now - timedelta(hours=2),
                    "status": "active"
                },
                "entities": [
                    {"name": "Turkish Coast Guard Command", "type": "organization"},
                    {"name": "Bosphorus Vessel Traffic Services", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-hurriyet-bosphorus-01",
                        "source_id": "src-hurriyet-tr",
                        "title": "Turkey deploys next-generation coastal radar system to monitor Bosphorus and Black Sea transit",
                        "url": "https://www.hurriyetdailynews.com/turkey-black-sea-maritime-radar",
                        "author": "Emre Aydin",
                        "published_at": now - timedelta(hours=10),
                        "raw_content": "The high-precision phased array sensors ensure collision-free transit for crude carriers and bulk grain freighters navigating congested straits.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 31: Afghanistan & Central Asian Border - Salang Commercial Transit Safety Protocol (Kabul, Afghanistan)
            {
                "event": {
                    "id": "evt-afghan-trans-hindu-kush-rail-2026",
                    "canonical_title": "Kabul and Central Asian Neighbors Sign Trans-Afghan Commercial Transit Safety Protocol",
                    "summary": "Regional commercial delegations in Kabul agreed on unified customs clearance and freight security standards for truck and rail convoys transiting the Salang corridor connecting Uzbekistan with South Asian trade routes.",
                    "category": "economy",
                    "subcategory": "trade_logistics",
                    "latitude": 34.53,
                    "longitude": 69.17,
                    "country": "Afghanistan",
                    "admin_region": "Kabul",
                    "city": "Kabul",
                    "location_confidence": 0.96,
                    "importance_score": 7.6,
                    "confidence_score": 0.90,
                    "human_impact_score": 7.8,
                    "global_impact_score": 7.2,
                    "economic_impact_score": 8.1,
                    "political_impact_score": 7.6,
                    "novelty_score": 7.7,
                    "development_velocity_score": 6.3,
                    "source_coverage_score": 8.1,
                    "first_seen_at": now - timedelta(hours=16),
                    "last_updated_at": now - timedelta(hours=5),
                    "status": "active"
                },
                "entities": [
                    {"name": "Afghanistan Chamber of Commerce and Investment", "type": "organization"},
                    {"name": "Central Asian Freight Operators Alliance", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-tolonews-transit-01",
                        "source_id": "src-tolonews-af",
                        "title": "Kabul signs multilateral transit security pact to unlock Northern trade corridor with Central Asia",
                        "url": "https://tolonews.com/afghan-central-asia-transit-protocol",
                        "author": "Zabihullah Ghazi",
                        "published_at": now - timedelta(hours=16),
                        "raw_content": "The protocol standardizes weigh station fees and introduces biometric clearance to expedite food grain and fuel transport across border crossings.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 32: Delhi-NCR (Hyper-Local / Ward & Municipal) - Real-time Air Quality Action Plan & EV Corridor
            {
                "event": {
                    "id": "evt-delhi-ncr-air-quality-2026",
                    "canonical_title": "Delhi-NCR Municipal Commission Deploys Ward-Level Automated Dust Suppression & Strict Zone-4 Traffic Curbs",
                    "summary": "The Commission for Air Quality Management (CAQM) and Delhi Municipal Corporation activated ward-level IoT smog towers and mandated non-electric commercial vehicle diversions across Anand Vihar, Connaught Place, and Noida arterial corridors to suppress seasonal PM2.5 concentrations.",
                    "category": "environment",
                    "subcategory": "air_quality",
                    "latitude": 28.61,
                    "longitude": 77.21,
                    "country": "India",
                    "admin_region": "Delhi",
                    "city": "New Delhi",
                    "location_confidence": 0.99,
                    "importance_score": 8.4,
                    "confidence_score": 0.95,
                    "human_impact_score": 8.9,
                    "global_impact_score": 7.3,
                    "economic_impact_score": 7.8,
                    "political_impact_score": 8.1,
                    "novelty_score": 8.0,
                    "development_velocity_score": 8.2,
                    "source_coverage_score": 9.2,
                    "first_seen_at": now - timedelta(hours=4),
                    "last_updated_at": now - timedelta(minutes=45),
                    "status": "developing"
                },
                "entities": [
                    {"name": "Commission for Air Quality Management", "type": "organization"},
                    {"name": "Municipal Corporation of Delhi", "type": "organization"},
                    {"name": "Central Pollution Control Board", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-ht-delhi-01",
                        "source_id": "src-hindustantimes-in",
                        "title": "Delhi launches hyper-local sensor network across 250 municipal wards to combat winter particulate spikes",
                        "url": "https://www.hindustantimes.com/cities/delhi-news/delhi-ward-air-quality-grid",
                        "author": "Soumya Pillai",
                        "published_at": now - timedelta(hours=4),
                        "raw_content": "The Municipal Corporation of Delhi deployed misting cannon trucks and dynamic electronic variable message signs across all major roundabouts.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-ndtv-delhi-02",
                        "source_id": "src-ndtv-in",
                        "title": "Delhi-NCR air index curbs: Commercial truck checkpoints operational on 12 border entry corridors",
                        "url": "https://www.ndtv.com/delhi-news/delhi-traffic-diversion-smog-guidelines",
                        "author": "NDTV News Desk",
                        "published_at": now - timedelta(hours=2, minutes=30),
                        "raw_content": "Traffic police teams in Gurugram, Faridabad, and Noida set up electronic RFID diversion bays for non-essential commercial vehicles.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 33: Mumbai (Hyper-Local / Coastal Municipal) - Mumbai Coastal Road Tunnel & High-Speed Connector
            {
                "event": {
                    "id": "evt-mumbai-coastal-road-2026",
                    "canonical_title": "Mumbai Municipal Corporation Opens Phase-2 Undersea Tunnel Linking Nariman Point to Bandra-Worli Sea Link",
                    "summary": "Brihanmumbai Municipal Corporation (BMC) inaugurated the twin undersea road tunnels between Marine Drive and Worli, slashing peak South Mumbai commute times by 70% with real-time acoustic fire safety monitoring.",
                    "category": "economy",
                    "subcategory": "urban_infrastructure",
                    "latitude": 18.92,
                    "longitude": 72.83,
                    "country": "India",
                    "admin_region": "Maharashtra",
                    "city": "Mumbai",
                    "location_confidence": 0.99,
                    "importance_score": 8.2,
                    "confidence_score": 0.94,
                    "human_impact_score": 8.6,
                    "global_impact_score": 7.5,
                    "economic_impact_score": 8.8,
                    "political_impact_score": 7.8,
                    "novelty_score": 8.1,
                    "development_velocity_score": 7.5,
                    "source_coverage_score": 8.9,
                    "first_seen_at": now - timedelta(hours=6),
                    "last_updated_at": now - timedelta(hours=1, minutes=15),
                    "status": "active"
                },
                "entities": [
                    {"name": "Brihanmumbai Municipal Corporation", "type": "organization"},
                    {"name": "Maharashtra State Road Development Corporation", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-ie-mumbai-01",
                        "source_id": "src-indianexpress-in",
                        "title": "Mumbai coastal road fully operational: Marine Drive to Worli commute cut to 10 minutes",
                        "url": "https://indianexpress.com/article/cities/mumbai/mumbai-coastal-road-phase-2-undersea-tunnel",
                        "author": "Clara Lewis",
                        "published_at": now - timedelta(hours=6),
                        "raw_content": "The subterranean expressway incorporates seismic dampers and automated ventilation shafts bored 20 meters beneath the Arabian Sea seabed.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-livemint-mumbai-02",
                        "source_id": "src-livemint-in",
                        "title": "Maharashtra infrastructure boom: Mumbai coastal highway opens, boosting western suburbs commercial logistics",
                        "url": "https://www.livemint.com/news/india/mumbai-coastal-road-traffic-telemetry",
                        "author": "Anirudh Laskar",
                        "published_at": now - timedelta(hours=3),
                        "raw_content": "Commercial real estate developers in Lower Parel and Worli reported surging corporate leasing following direct arterial highway connectivity.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 34: Bengaluru (Hyper-Local / Tech Corridor) - Outer Ring Road Autonomous Feeder Shuttles & Metro Interchange
            {
                "event": {
                    "id": "evt-bengaluru-orr-transit-2026",
                    "canonical_title": "Bengaluru Outer Ring Road Companies Alliance Launches Autonomous Electric Bus Feeders & Silk Board Interchange",
                    "summary": "The Bangalore Metropolitan Transport Corporation (BMTC) partnered with Whitefield and Bellandur IT corridors to deploy 120 dedicated electric feeder shuttles directly synchronized with the newly commissioned Yellow Line metro interchange.",
                    "category": "science_technology",
                    "subcategory": "smart_transit",
                    "latitude": 12.97,
                    "longitude": 77.59,
                    "country": "India",
                    "admin_region": "Karnataka",
                    "city": "Bengaluru",
                    "location_confidence": 0.98,
                    "importance_score": 8.0,
                    "confidence_score": 0.92,
                    "human_impact_score": 8.5,
                    "global_impact_score": 7.7,
                    "economic_impact_score": 8.5,
                    "political_impact_score": 7.4,
                    "novelty_score": 8.3,
                    "development_velocity_score": 7.1,
                    "source_coverage_score": 8.7,
                    "first_seen_at": now - timedelta(hours=8),
                    "last_updated_at": now - timedelta(hours=2),
                    "status": "active"
                },
                "entities": [
                    {"name": "Bangalore Metropolitan Transport Corporation", "type": "organization"},
                    {"name": "Outer Ring Road Companies Association", "type": "organization"},
                    {"name": "Namma Metro", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-dh-bengaluru-01",
                        "source_id": "src-deccanherald-in",
                        "title": "Bengaluru tech corridor traffic respite: 120 EV feeder buses operational along Bellandur and Outer Ring Road",
                        "url": "https://www.deccanherald.com/india/karnataka/bengaluru/outer-ring-road-smart-shuttles",
                        "author": "Rasheed Kappan",
                        "published_at": now - timedelta(hours=8),
                        "raw_content": "The low-floor accessible electric buses operate at 4-minute intervals connecting major tech parks directly to the Silk Board elevated metro hub.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-thehindu-bengaluru-02",
                        "source_id": "src-thehindu-in",
                        "title": "Bengaluru Smart City initiative integrates contactless ticketing across Namma Metro and corporate tech parks",
                        "url": "https://www.thehindu.com/news/cities/bangalore/bengaluru-silk-board-interchange-ev",
                        "author": "K.V. Aditya Bharadwaj",
                        "published_at": now - timedelta(hours=4),
                        "raw_content": "Tech employees can tap standard corporate smartcards to access both intra-park shuttles and rapid transit trains.",
                        "relationship_type": "corroborating"
                    }
                ]
            },

            # SCENARIO 35: Chennai (State & Maritime Port) - Ennore Deep-Water Green Ammonia & Hydrogen Bunkering Artery
            {
                "event": {
                    "id": "evt-chennai-ennore-port-2026",
                    "canonical_title": "Tamil Nadu Maritime Board Commissions Green Hydrogen Bunkering Terminal at Chennai Kamarajar Port",
                    "summary": "Tamil Nadu maritime infrastructure authorities and international shipping consortiums opened India's first zero-carbon marine bunkering jetty at Ennore, capable of refueling 40 deep-sea container vessels monthly.",
                    "category": "economy",
                    "subcategory": "maritime_trade",
                    "latitude": 13.08,
                    "longitude": 80.27,
                    "country": "India",
                    "admin_region": "Tamil Nadu",
                    "city": "Chennai",
                    "location_confidence": 0.98,
                    "importance_score": 7.9,
                    "confidence_score": 0.91,
                    "human_impact_score": 7.4,
                    "global_impact_score": 8.1,
                    "economic_impact_score": 8.7,
                    "political_impact_score": 7.6,
                    "novelty_score": 8.2,
                    "development_velocity_score": 6.4,
                    "source_coverage_score": 8.4,
                    "first_seen_at": now - timedelta(hours=10),
                    "last_updated_at": now - timedelta(hours=3),
                    "status": "active"
                },
                "entities": [
                    {"name": "Tamil Nadu Maritime Board", "type": "organization"},
                    {"name": "Kamarajar Port Limited", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-thehindu-chennai-01",
                        "source_id": "src-thehindu-in",
                        "title": "Chennai's Kamarajar Port becomes first in South Asia to initiate commercial green ammonia ship bunkering",
                        "url": "https://www.thehindu.com/news/national/tamil-nadu/chennai-ennore-green-bunkering",
                        "author": "Sunitha Sekar",
                        "published_at": now - timedelta(hours=10),
                        "raw_content": "The cryogenic fuel storage farm is directly linked to offshore solar-powered electrolyzers along the Coromandel coastline.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 36: Kolkata (Municipal & Riverine) - East-West Under-River Metro Expansion & Hooghly Flood Barrier Network
            {
                "event": {
                    "id": "evt-kolkata-metro-hooghly-2026",
                    "canonical_title": "Kolkata Metro Extends Underwater Hooghly River Service to Howrah Station with Automated Sluice Flood Gates",
                    "summary": "Kolkata Metro Rail Corporation (KMRC) and civil flood engineers activated 14 pneumatic floodgate chambers along the Hooghly river tunnel, safeguarding high-frequency passenger transit beneath the river during monsoon surges.",
                    "category": "science_technology",
                    "subcategory": "civil_engineering",
                    "latitude": 22.57,
                    "longitude": 88.36,
                    "country": "India",
                    "admin_region": "West Bengal",
                    "city": "Kolkata",
                    "location_confidence": 0.99,
                    "importance_score": 8.1,
                    "confidence_score": 0.93,
                    "human_impact_score": 8.7,
                    "global_impact_score": 7.6,
                    "economic_impact_score": 8.4,
                    "political_impact_score": 7.7,
                    "novelty_score": 8.1,
                    "development_velocity_score": 6.8,
                    "source_coverage_score": 8.6,
                    "first_seen_at": now - timedelta(hours=11),
                    "last_updated_at": now - timedelta(hours=3, minutes=30),
                    "status": "active"
                },
                "entities": [
                    {"name": "Kolkata Metro Rail Corporation", "type": "organization"},
                    {"name": "Howrah Municipal Corporation", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-telegraph-kolkata-01",
                        "source_id": "src-telegraph-in",
                        "title": "Kolkata underwater metro increases peak frequency across Howrah corridor; automated Hooghly flood monitors active",
                        "url": "https://www.telegraphindia.com/west-bengal/calcutta/kolkata-underwater-metro-howrah-frequency",
                        "author": "Subhajoy Roy",
                        "published_at": now - timedelta(hours=11),
                        "raw_content": "The state-of-the-art tunnel sensors transmit telemetry to central command at 500-millisecond intervals to detect any moisture variations.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 37: Hyderabad (Regional & Biotech) - Genome Valley AI-Powered Biopharmaceutical Cluster Expansion
            {
                "event": {
                    "id": "evt-hyderabad-genome-valley-2026",
                    "canonical_title": "Telangana Expands Hyderabad Genome Valley with $1.4B Automated Biologics & AI Drug Discovery Campus",
                    "summary": "Telangana state government and global pharmaceutical research alliances opened Phase-4 of Genome Valley in Hyderabad, introducing robotic formulation labs and a centralized cold-chain logistics park.",
                    "category": "science_technology",
                    "subcategory": "biotechnology",
                    "latitude": 17.38,
                    "longitude": 78.48,
                    "country": "India",
                    "admin_region": "Telangana",
                    "city": "Hyderabad",
                    "location_confidence": 0.98,
                    "importance_score": 7.8,
                    "confidence_score": 0.91,
                    "human_impact_score": 7.9,
                    "global_impact_score": 8.2,
                    "economic_impact_score": 8.6,
                    "political_impact_score": 7.5,
                    "novelty_score": 8.0,
                    "development_velocity_score": 6.5,
                    "source_coverage_score": 8.3,
                    "first_seen_at": now - timedelta(hours=13),
                    "last_updated_at": now - timedelta(hours=4),
                    "status": "active"
                },
                "entities": [
                    {"name": "Telangana Life Sciences Advisory Committee", "type": "organization"},
                    {"name": "Genome Valley Bio-Cluster", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-ie-hyderabad-01",
                        "source_id": "src-indianexpress-in",
                        "title": "Hyderabad Genome Valley Phase-4 inaugurated: Telangana solidifies global life sciences manufacturing leadership",
                        "url": "https://indianexpress.com/article/cities/hyderabad/hyderabad-genome-valley-expansion",
                        "author": "Sreenivas Janyala",
                        "published_at": now - timedelta(hours=13),
                        "raw_content": "The campus integrates cleanrooms with high-performance computing clusters designed for accelerated vaccine candidate synthesis.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 38: Ahmedabad (Regional Transport) - Mumbai-Ahmedabad High Speed Rail Sabarmati Multimodal Transit Terminal
            {
                "event": {
                    "id": "evt-ahmedabad-bullet-train-2026",
                    "canonical_title": "National High Speed Rail Corporation Completes Sabarmati Multimodal Bullet Train Terminal in Ahmedabad",
                    "summary": "High-speed rail engineers in Ahmedabad completed the central terminal building for the Mumbai-Ahmedabad bullet train corridor, connecting high-speed rail with Western Railway broad-gauge platforms and Ahmedabad BRTS buses.",
                    "category": "economy",
                    "subcategory": "rail_transport",
                    "latitude": 23.02,
                    "longitude": 72.57,
                    "country": "India",
                    "admin_region": "Gujarat",
                    "city": "Ahmedabad",
                    "location_confidence": 0.98,
                    "importance_score": 8.3,
                    "confidence_score": 0.93,
                    "human_impact_score": 8.4,
                    "global_impact_score": 8.0,
                    "economic_impact_score": 8.9,
                    "political_impact_score": 8.0,
                    "novelty_score": 8.2,
                    "development_velocity_score": 7.0,
                    "source_coverage_score": 8.8,
                    "first_seen_at": now - timedelta(hours=14),
                    "last_updated_at": now - timedelta(hours=4, minutes=15),
                    "status": "active"
                },
                "entities": [
                    {"name": "National High Speed Rail Corporation", "type": "organization"},
                    {"name": "Gujarat Metro Rail Corporation", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-livemint-ahmedabad-01",
                        "source_id": "src-livemint-in",
                        "title": "Sabarmati bullet train terminal ready: Integrated ticketing to link Ahmedabad metro, railway, and high-speed rail",
                        "url": "https://www.livemint.com/news/india/ahmedabad-sabarmati-bullet-train-hub",
                        "author": "Shayan Ghosh",
                        "published_at": now - timedelta(hours=14),
                        "raw_content": "The terminal features roof-top photovoltaic arrays and automated luggage transfer belts directly connecting airport shuttle bays.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 39: Kochi (Hyper-Local Island Transit) - Kochi Water Metro 10-Island Clean Ferry Grid Expansion
            {
                "event": {
                    "id": "evt-kochi-water-metro-2026",
                    "canonical_title": "Kochi Water Metro Extends All-Electric Ferry Services to 10 Additional Island Terminals",
                    "summary": "Kochi Metro Rail Limited (KMRL) expanded its battery-electric catamaran ferry fleet to cover Vypin, Bolgatty, and Mattancherry, providing affordable solar-powered water transport to over 80,000 daily island commuters.",
                    "category": "environment",
                    "subcategory": "green_mobility",
                    "latitude": 9.93,
                    "longitude": 76.27,
                    "country": "India",
                    "admin_region": "Kerala",
                    "city": "Kochi",
                    "location_confidence": 0.98,
                    "importance_score": 7.7,
                    "confidence_score": 0.92,
                    "human_impact_score": 8.3,
                    "global_impact_score": 7.4,
                    "economic_impact_score": 8.1,
                    "political_impact_score": 7.5,
                    "novelty_score": 8.0,
                    "development_velocity_score": 6.3,
                    "source_coverage_score": 8.2,
                    "first_seen_at": now - timedelta(hours=15),
                    "last_updated_at": now - timedelta(hours=5),
                    "status": "active"
                },
                "entities": [
                    {"name": "Kochi Metro Rail Limited", "type": "organization"},
                    {"name": "Kerala State Inland Navigation Corporation", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-mathrubhumi-kochi-01",
                        "source_id": "src-mathrubhumi-in",
                        "title": "Kochi Water Metro expands fleet to 10 more terminals; eco-friendly water transport brings islanders closer to city mainland",
                        "url": "https://english.mathrubhumi.com/news/kerala/kochi-water-metro-ten-new-terminals",
                        "author": "Anil Radhakrishnan",
                        "published_at": now - timedelta(hours=15),
                        "raw_content": "The silent battery-powered vessels feature air-conditioned cabins and dedicated floating pontoons that rise and fall with sea tides.",
                        "relationship_type": "primary"
                    }
                ]
            },

            # SCENARIO 40: Guwahati / Northeast (Disaster Resilience & Regional Riverine) - Brahmaputra Basin Real-Time Sensor Telemetry Net
            {
                "event": {
                    "id": "evt-guwahati-brahmaputra-flood-2026",
                    "canonical_title": "Assam Disaster Management Authority Installs 85 Acoustic River Sensors Across Brahmaputra Basin in Guwahati",
                    "summary": "Hydrologists and state emergency response teams along the Brahmaputra river installed high-precision acoustic doppler riverbed profilers and solar telemetry stations in Guwahati to provide 48-hour advance flash flood warnings to over 3 million riverbank residents.",
                    "category": "natural_disaster",
                    "subcategory": "flood_early_warning",
                    "latitude": 26.14,
                    "longitude": 91.73,
                    "country": "India",
                    "admin_region": "Assam",
                    "city": "Guwahati",
                    "location_confidence": 0.98,
                    "importance_score": 8.5,
                    "confidence_score": 0.94,
                    "human_impact_score": 9.1,
                    "global_impact_score": 7.8,
                    "economic_impact_score": 8.4,
                    "political_impact_score": 7.9,
                    "novelty_score": 8.3,
                    "development_velocity_score": 7.6,
                    "source_coverage_score": 8.7,
                    "first_seen_at": now - timedelta(hours=17),
                    "last_updated_at": now - timedelta(hours=5, minutes=30),
                    "status": "active"
                },
                "entities": [
                    {"name": "Assam State Disaster Management Authority", "type": "organization"},
                    {"name": "Brahmaputra Board", "type": "organization"},
                    {"name": "Central Water Commission", "type": "organization"}
                ],
                "articles": [
                    {
                        "id": "art-ht-guwahati-01",
                        "source_id": "src-hindustantimes-in",
                        "title": "Assam deploys automated Doppler river-depth sensors in Brahmaputra to eliminate flash-flood blind spots",
                        "url": "https://www.hindustantimes.com/india-news/assam-brahmaputra-flood-telemetry-grid",
                        "author": "Utpal Parashar",
                        "published_at": now - timedelta(hours=17),
                        "raw_content": "The ultrasonic transducers detect sudden embankment erosion and silt accumulation, alerting village panchayats via SMS siren relays.",
                        "relationship_type": "primary"
                    }
                ]
            }
        ]

        total_events_created = 0
        total_articles_created = 0
        total_entities_created = 0

        # Insert Events, Articles, Entities, and Associations
        for item in scenarios:
            evt_data = item["event"]
            existing_event = (await session.execute(select(Event).where(Event.id == evt_data["id"]))).scalar_one_or_none()
            if not existing_event:
                event = Event(**evt_data)
                session.add(event)
                await session.flush()
                total_events_created += 1
            else:
                event = existing_event

            # Seed Event Entities
            for ent_data in item.get("entities", []):
                ent_name = ent_data["name"]
                norm_name = ent_name.lower().strip()
                existing_entity = (await session.execute(
                    select(Entity).where(Entity.normalized_name == norm_name)
                )).scalar_one_or_none()

                if not existing_entity:
                    entity = Entity(
                        name=ent_name,
                        entity_type=ent_data.get("type", "concept"),
                        normalized_name=norm_name
                    )
                    session.add(entity)
                    await session.flush()
                    total_entities_created += 1
                else:
                    entity = existing_entity

                # Link Event to Entity
                existing_ee_link = (await session.execute(
                    select(EventEntity).where(
                        EventEntity.event_id == event.id,
                        EventEntity.entity_id == entity.id
                    )
                )).scalar_one_or_none()

                if not existing_ee_link:
                    ee_link = EventEntity(
                        event_id=event.id,
                        entity_id=entity.id
                    )
                    session.add(ee_link)

            # Seed Articles
            for art_data in item["articles"]:
                rel_type = art_data.pop("relationship_type", "corroborating")
                canonical_url = normalize_url(art_data["url"])
                clean_t = clean_text(art_data["title"])
                clean_c = clean_text(art_data["raw_content"])
                t_hash, c_hash = compute_hashes(clean_t, clean_c)

                existing_article = (await session.execute(
                    select(Article).where(
                        or_(Article.id == art_data["id"], Article.url == art_data["url"])
                    )
                )).scalar_one_or_none()
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
                    total_articles_created += 1
                else:
                    article = existing_article
                    article.url = art_data["url"]
                    article.canonical_url = canonical_url

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
        print(f"--> [SEED COMPLETE] Successfully verified database: {len(scenarios)} Events, multiple articles & entities populated across 6 continents.")


if __name__ == "__main__":
    asyncio.run(seed_database())
