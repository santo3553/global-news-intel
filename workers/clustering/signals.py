import math
from datetime import datetime, timezone
from typing import Set, Tuple, Optional, Dict, Any
from workers.embeddings.embedding_engine import cosine_similarity


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the great-circle distance between two points on Earth in kilometers.
    """
    r = 6371.0  # Earth's radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def compute_geographic_similarity(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float],
    half_decay_distance_km: float = 200.0
) -> float:
    """
    Computes smooth geographic proximity score between 0.0 and 1.0.
    - If coordinates are identical: 1.0
    - Within 25km: ~0.95+
    - At half_decay_distance_km (e.g. 200km): ~0.50
    - If either coordinate is missing: 0.50 neutral baseline
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.50

    distance_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    # Exponential decay formula
    similarity = math.exp(-0.69315 * (distance_km / max(1.0, half_decay_distance_km)))
    return max(0.0, min(1.0, round(similarity, 4)))


def compute_temporal_similarity(
    time1: datetime,
    time2: datetime,
    max_window_hours: float = 72.0
) -> float:
    """
    Computes temporal proximity score between 0.0 and 1.0.
    Articles published close together score near 1.0; decays smoothly over the time window.
    """
    if time1.tzinfo is None:
        time1 = time1.replace(tzinfo=timezone.utc)
    if time2.tzinfo is None:
        time2 = time2.replace(tzinfo=timezone.utc)

    delta_seconds = abs((time1 - time2).total_seconds())
    delta_hours = delta_seconds / 3600.0

    if delta_hours > max_window_hours:
        return 0.0

    similarity = math.exp(-0.69315 * (delta_hours / (max_window_hours / 2.0)))
    return max(0.0, min(1.0, round(similarity, 4)))


def compute_entity_similarity(entities_a: Set[str], entities_b: Set[str]) -> float:
    """
    Jaccard overlap between two sets of normalized entity names.
    """
    if not entities_a or not entities_b:
        return 0.0
    intersection = len(entities_a.intersection(entities_b))
    union = len(entities_a.union(entities_b))
    if union == 0:
        return 0.0
    return round(intersection / union, 4)


def compute_category_similarity(cat_a: str, cat_b: str, subcat_a: Optional[str] = None, subcat_b: Optional[str] = None) -> float:
    """
    Category compatibility score.
    """
    if not cat_a or not cat_b:
        return 0.50

    cat_a = cat_a.lower().strip()
    cat_b = cat_b.lower().strip()

    if cat_a == cat_b:
        if subcat_a and subcat_b and subcat_a.lower().strip() == subcat_b.lower().strip():
            return 1.0
        return 0.90

    # Cross-category affinities (e.g. natural disaster & environment, politics & security)
    related_pairs = {
        ("natural_disaster", "environment"),
        ("politics", "security"),
        ("politics", "economy"),
        ("science", "environment"),
        ("health", "society")
    }
    if (cat_a, cat_b) in related_pairs or (cat_b, cat_a) in related_pairs:
        return 0.40

    return 0.0


def compute_composite_cluster_score(
    semantic_sim: float,
    geo_sim: float,
    entity_sim: float,
    temporal_sim: float,
    category_sim: float,
    w_sem: float = 0.40,
    w_geo: float = 0.20,
    w_ent: float = 0.15,
    w_time: float = 0.15,
    w_cat: float = 0.10
) -> float:
    """
    Computes multi-signal composite clustering score according to Section 14 formula:
    cluster_score = w_sem * semantic + w_geo * geo + w_ent * entity + w_time * time + w_cat * category
    """
    score = (
        w_sem * semantic_sim
        + w_geo * geo_sim
        + w_ent * entity_sim
        + w_time * temporal_sim
        + w_cat * category_sim
    )
    return max(0.0, min(1.0, round(score, 4)))
