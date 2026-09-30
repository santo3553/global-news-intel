import pytest
from datetime import datetime, timezone, timedelta
from workers.clustering.signals import (
    haversine_distance_km,
    compute_geographic_similarity,
    compute_temporal_similarity,
    compute_entity_similarity,
    compute_category_similarity,
    compute_composite_cluster_score
)


def test_haversine_distance():
    # Tokyo (35.68, 139.76) to Osaka (34.69, 135.50) is ~400 km
    dist = haversine_distance_km(35.68, 139.76, 34.69, 135.50)
    assert 380.0 < dist < 420.0

    # Same location distance is 0 km
    assert haversine_distance_km(35.0, 135.0, 35.0, 135.0) == 0.0


def test_geographic_similarity():
    # Identical coordinates
    assert compute_geographic_similarity(32.8, 131.0, 32.8, 131.0) == 1.0

    # Near coordinates (~15 km apart)
    sim_close = compute_geographic_similarity(31.91, 131.42, 31.95, 131.45)
    assert sim_close > 0.90

    # Distant coordinates (Tokyo to London)
    sim_far = compute_geographic_similarity(35.68, 139.76, 51.50, -0.12)
    assert sim_far < 0.01


def test_temporal_similarity():
    now = datetime.now(timezone.utc)
    # Same timestamp
    assert compute_temporal_similarity(now, now) == 1.0

    # 4 hours apart
    sim_4h = compute_temporal_similarity(now, now - timedelta(hours=4))
    assert sim_4h > 0.85

    # 24 hours apart
    sim_24h = compute_temporal_similarity(now, now - timedelta(hours=24))
    assert 0.50 < sim_24h < 0.75

    # Outside 72h window
    sim_out = compute_temporal_similarity(now, now - timedelta(hours=80), max_window_hours=72.0)
    assert sim_out == 0.0


def test_entity_similarity():
    entities1 = {"japan", "tokyo", "reuters", "meteorological agency"}
    entities2 = {"japan", "tokyo", "nhk", "meteorological agency"}
    entities3 = {"france", "paris", "baguette"}

    sim_high = compute_entity_similarity(entities1, entities2)
    sim_zero = compute_entity_similarity(entities1, entities3)

    assert sim_high >= 0.60
    assert sim_zero == 0.0


def test_category_similarity():
    # Exact category and subcategory
    assert compute_category_similarity("natural_disaster", "natural_disaster", "earthquake", "earthquake") == 1.0

    # Same category, different subcategory
    assert compute_category_similarity("natural_disaster", "natural_disaster", "earthquake", "flood") == 0.90

    # Related domains
    assert compute_category_similarity("politics", "security") == 0.40

    # Unrelated domains
    assert compute_category_similarity("natural_disaster", "economy") == 0.0


def test_composite_score():
    score = compute_composite_cluster_score(
        semantic_sim=0.90,
        geo_sim=0.95,
        entity_sim=0.80,
        temporal_sim=0.90,
        category_sim=1.0,
        w_sem=0.40,
        w_geo=0.20,
        w_ent=0.15,
        w_time=0.15,
        w_cat=0.10
    )
    # 0.4*0.9 + 0.2*0.95 + 0.15*0.8 + 0.15*0.9 + 0.1*1.0 = 0.36 + 0.19 + 0.12 + 0.135 + 0.1 = 0.905
    assert 0.89 < score < 0.92
