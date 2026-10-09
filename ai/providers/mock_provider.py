import re
import math
import hashlib
from typing import List
from ai.providers.base import AIProvider
from ai.schemas.extraction import ExtractedEventData, ExtractedLocation, ExtractedEntity


class MockAIProvider(AIProvider):
    """
    Deterministic rule-based AI provider for local testing, CI, and instant offline operation.
    Generates structured Pydantic event data and dense 384-dimensional embeddings.
    """

    async def extract_event(self, title: str, text: str) -> ExtractedEventData:
        combined = f"{title} {text}".lower()

        # 1. Category and Subcategory Detection
        category = "general"
        subcategory = None
        severity = 0.5
        human_impact = 5.0
        global_impact = 5.0
        novelty = 0.6

        if any(w in combined for w in ["earthquake", "quake", "tremor", "tsunami", "flood", "hurricane", "typhoon", "wildfire", "volcano"]):
            category = "natural_disaster"
            if "earthquake" in combined or "quake" in combined or "tremor" in combined:
                subcategory = "earthquake"
                severity = 0.85
                human_impact = 8.0
                global_impact = 7.5
                novelty = 0.8
            elif "tsunami" in combined:
                subcategory = "tsunami"
                severity = 0.90
                human_impact = 8.5
        elif any(w in combined for w in ["summit", "accord", "treaty", "election", "vote", "parliament", "president", "diplomat", "ratify"]):
            category = "politics"
            subcategory = "diplomacy" if "summit" in combined or "treaty" in combined or "accord" in combined else "election"
            severity = 0.40
            human_impact = 6.0
            global_impact = 8.5
            novelty = 0.7
        elif any(w in combined for w in ["security", "sabotage", "drone", "missile", "military", "defense", "interconnector", "fluctuation"]):
            category = "security"
            subcategory = "infrastructure" if "grid" in combined or "interconnector" in combined else "defense"
            severity = 0.70
            human_impact = 6.5
            global_impact = 7.0
            novelty = 0.75
        elif any(w in combined for w in ["telescope", "nasa", "exoplanet", "astronomy", "discovery", "space", "orbit"]):
            category = "science"
            subcategory = "astronomy"
            severity = 0.20
            human_impact = 3.5
            global_impact = 8.0
            novelty = 0.95
        elif any(w in combined for w in ["trade", "mercosur", "tariff", "asean", "economy", "inflation", "gdp", "market"]):
            category = "economy"
            subcategory = "trade"
            severity = 0.35
            human_impact = 5.5
            global_impact = 7.2
            novelty = 0.65

        # 2. Location Detection using comprehensive offline gazetteer
        from workers.extraction.geocoder import Geocoder
        geocoder = Geocoder()
        resolved = geocoder.resolve(
            raw_name="",
            country_hint=None,
            text_context=combined
        )

        location = ExtractedLocation(
            name=resolved.name,
            country=resolved.country,
            admin_region=resolved.admin_region,
            city=resolved.city,
            latitude=resolved.latitude,
            longitude=resolved.longitude,
            precision=resolved.precision,
            location_confidence=resolved.location_confidence
        )

        # 3. Entities
        entities: List[ExtractedEntity] = []
        if resolved.country:
            entities.append(ExtractedEntity(name=resolved.country, type="country"))
        if resolved.city:
            entities.append(ExtractedEntity(name=resolved.city, type="location"))

        for org in ["Reuters", "Associated Press", "BBC", "NHK", "NASA", "UN", "Mercosur", "ASEAN", "European Union", "JMA"]:
            if org.lower() in combined:
                entities.append(ExtractedEntity(name=org, type="organization"))

        # 4. Factual Claims
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 20]
        claims = sentences[:4] if sentences else [title]

        return ExtractedEventData(
            event_title=title.strip(),
            category=category,
            subcategory=subcategory,
            location=location,
            entities=entities,
            claims=claims,
            severity=severity,
            novelty=novelty,
            confidence=0.90 if len(entities) > 1 else 0.75,
            human_impact_estimate=human_impact,
            global_impact_estimate=global_impact
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic 384-dimensional unit-normalized embedding vector.
        Combines token hashing, sub-character trigrams, and semantic concept clustering.
        """
        dim = 384
        vec = [0.0] * dim
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        tokens = re.findall(r"\b\w{3,}\b", normalized)

        # Trigrams and tokens hashed into 384 buckets
        for token in tokens:
            # Word bucket
            h_word = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
            vec[h_word] += 1.0

            # Sub-character trigrams
            for i in range(len(token) - 2):
                trigram = token[i:i + 3]
                h_tri = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16) % dim
                vec[h_tri] += 0.3

        # Semantic Concept Clusters (simulates dense embeddings for related concepts)
        SEMANTIC_CLUSTERS = {
            "seismic_disaster": ["earthquake", "quake", "tremor", "tsunami", "seismic", "aftershock", "epicenter", "kyushu", "miyazaki"],
            "storm_disaster": ["hurricane", "typhoon", "cyclone", "storm", "flood", "wildfire"],
            "diplomacy_accord": ["treaty", "summit", "accord", "diplomat", "negotiate", "consensus", "climate", "geneva"],
            "security_conflict": ["military", "missile", "drone", "sabotage", "attack", "defense", "security", "baltic", "interconnector"],
            "space_science": ["telescope", "exoplanet", "nasa", "astronomy", "satellite", "space"],
            "economic_trade": ["tariff", "trade", "mercosur", "inflation", "market", "economy", "argentina"]
        }

        for cluster_name, keywords in SEMANTIC_CLUSTERS.items():
            matched = sum(1 for kw in keywords if kw in normalized)
            if matched > 0:
                h_cluster = int(hashlib.md5(cluster_name.encode("utf-8")).hexdigest(), 16) % dim
                # Boost semantic concept dimensions
                for offset in range(4):
                    vec[(h_cluster + offset) % dim] += 1.5 * matched

        # L2 Unit Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]
        else:
            vec[0] = 1.0

        return vec

    async def summarize_event(self, prompt: str) -> str:
        return (
            "### What Happened?\n"
            "A notable event was recorded and verified by multiple reporting sources.\n\n"
            "### Why It Matters\n"
            "This development has regional and global implications for civil infrastructure and policy.\n\n"
            "### What Is Known\n"
            "* Multiple independent sources have confirmed initial reports.\n"
            "* Regional monitoring services are actively tracking developments.\n\n"
            "### What Is Uncertain\n"
            "* Long-term secondary effects and comprehensive impact assessments are ongoing."
        )
