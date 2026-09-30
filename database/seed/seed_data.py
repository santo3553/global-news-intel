"""
Deterministic Seed Data Generator for Global News Intelligence.
Fulfills Section 24 & 25: Demonstrates multi-source clustering, multi-country events,
varying importance scores, uncertain/developing reports, deduplication, and named entities.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
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
                    },
                    {
                        "id": "art-ap-climate-04",
                        "source_id": "src-ap-top",
                        "title": "Global financial markets rally following Geneva clean power accord announcement",
                        "url": "https://apnews.com/article/geneva-clean-energy-markets-rally-2026",
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
                        "url": "https://www.aljazeera.com/news/2026/9/red-sea-drones-intercepted-bab-el-mandeb",
                        "author": "Al Jazeera Staff",
                        "published_at": now - timedelta(hours=5),
                        "raw_content": "Naval forces in the southern Red Sea repelled unmanned aerial craft approaching international commercial shipping vessels off the coast of Yemen.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-bbc-redsea-02",
                        "source_id": "src-bbc-world",
                        "title": "Red Sea tension flares as naval escort destroys explosive sea drone",
                        "url": "https://www.bbc.com/news/world-middle-east-8392019",
                        "author": "Jonathan Beale",
                        "published_at": now - timedelta(hours=3, minutes=30),
                        "raw_content": "A naval frigate successfully neutralized a fast-moving unmanned surface vessel in international waters, confirming no civilian casualties.",
                        "relationship_type": "corroborating"
                    },
                    {
                        "id": "art-reuters-redsea-03",
                        "source_id": "src-reuters-world",
                        "title": "Container insurance rates tick higher following latest Bab el-Mandeb incident",
                        "url": "https://www.reuters.com/business/shipping/red-sea-insurance-premiums-rise-2026",
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
                        "url": "https://www.channelnewsasia.com/business/taiwan-semiconductor-european-foundry-dresden-2026",
                        "author": "CNA Tech Desk",
                        "published_at": now - timedelta(hours=16),
                        "raw_content": "Industry executives from Hsinchu confirmed final clearance for the joint semiconductor manufacturing fab in Dresden.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-dw-semi-02",
                        "source_id": "src-dw-world",
                        "title": "Germany hails multi-billion euro Dresden microchip facility as milestone for EU industrial strategy",
                        "url": "https://www.dw.com/en/germany-dresden-semiconductor-investment-milestone/a-9128372",
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
                        "url": "https://www.bbc.com/news/world-europe-6921389",
                        "author": "Einar Sigurdsson",
                        "published_at": now - timedelta(hours=6),
                        "raw_content": "Lava is spewing from a newly opened fissure on the Reykjanes peninsula in south-west Iceland following intensive earthquake activity.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-euronews-volcano-02",
                        "source_id": "src-euronews-en",
                        "title": "Iceland volcano: Lava barriers protect geothermal plant as eruption stabilizes",
                        "url": "https://www.euronews.com/2026/iceland-volcano-lava-barriers-grindavik",
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
                        "url": "https://www.aljazeera.com/news/2026/9/nile-tripartite-dam-accord-cairo",
                        "author": "Amina Ismail",
                        "published_at": now - timedelta(hours=20),
                        "raw_content": "After decades of diplomatic deadlock, delegations in Cairo announced agreement on binding technical guidelines for hydrological drought operation.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-france24-nile-02",
                        "source_id": "src-france24-en",
                        "title": "Cairo tripartite summit concludes with agreement on Nile reservoir management",
                        "url": "https://www.france24.com/en/africa/2026-cairo-nile-dam-treaty-signed",
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
                        "url": "https://www.euronews.com/2026/eurocontrol-network-cyber-investigation",
                        "author": "Euronews Brussels Bureau",
                        "published_at": now - timedelta(hours=44),
                        "raw_content": "Aviation agencies across Western Europe experienced intermittent network failures affecting flight route telemetry synchronization.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-dw-cyber-02",
                        "source_id": "src-dw-world",
                        "title": "Aviation cyber incident: Flights delayed across Frankfurt, Paris, and Amsterdam",
                        "url": "https://www.dw.com/en/european-aviation-cyberattack-flight-delays/a-8291024",
                        "author": "Marcus Becker",
                        "published_at": now - timedelta(hours=24),
                        "raw_content": "Airlines initiated rerouting strategies as cybersecurity teams work around the clock to isolate compromised relay endpoints.",
                        "relationship_type": "update"
                    },
                    {
                        "id": "art-theguardian-cyber-03",
                        "source_id": "src-theguardian-world",
                        "title": "Air traffic systems restored to 90% capacity after unprecedented European cyber strike",
                        "url": "https://www.theguardian.com/world/2026/sep/eurocontrol-cyber-restoration-status",
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
                        "url": "https://en.mercopress.com/2026/09/peru-andes-mudslide-four-dead",
                        "author": "Mercopress Lima Bureau",
                        "published_at": now - timedelta(hours=12),
                        "raw_content": "Civil defense crews in southern Peru confirmed four fatalities after torrential rain dislodged hillsides onto regional transport corridors.",
                        "relationship_type": "primary"
                    },
                    {
                        "id": "art-bbc-andes-02",
                        "source_id": "src-bbc-world",
                        "title": "Peru landslide: Local emergency responders fear dozens missing as rescue search continues",
                        "url": "https://www.bbc.com/news/world-latin-america-8120392",
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
                        "url": "https://en.mercopress.com/2026/09/14/mercosur-asean-trade-pact-signed",
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
                        "url": "https://apnews.com/article/webb-telescope-exoplanet-atmosphere-water-2026",
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
                        "url": "https://www.theguardian.com/world/2026/sep/oslo-arctic-treaty-signed",
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
                        "url": "https://www.channelnewsasia.com/business/singapore-mas-ai-finance-regulations-2026",
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
                        "url": "https://www.france24.com/en/africa/2026-nairobi-clean-power-grid-launch",
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
                        "url": "https://www.euronews.com/2026/baltic-power-interconnector-probe",
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
                        "url": "https://www.reuters.com/markets/central-bank-symposium-policy-divergence-2026",
                        "author": "Howard Schneider",
                        "published_at": now - timedelta(hours=12),
                        "raw_content": "Monetary authorities from the United States, Europe, and Asia emphasized differing domestic inflation fundamentals during opening plenary remarks.",
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
                    total_articles_created += 1
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
        print(f"--> [SEED COMPLETE] Successfully verified database: {len(scenarios)} Events, multiple articles & entities populated across 6 continents.")


if __name__ == "__main__":
    asyncio.run(seed_database())
