import pytest
from datetime import datetime, timezone, timedelta
from workers.ranking.impact_scorer import (
    compute_event_importance,
    calculate_geographic_scope,
    calculate_source_coverage_score,
    calculate_development_velocity,
    ImpactScores
)


def test_geographic_scope_resolution():
    # Local city scope
    score_city = calculate_geographic_scope(city="Geneva", admin_region="Canton of Geneva", country="Switzerland")
    assert score_city == 3.0

    # Regional scope
    score_reg = calculate_geographic_scope(city=None, admin_region="Bavaria", country="Germany")
    assert score_reg == 5.5

    # Country scope
    score_country = calculate_geographic_scope(city=None, admin_region=None, country="Japan")
    assert score_country == 7.5

    # Global category
    score_climate = calculate_geographic_scope(city="Paris", admin_region=None, country="France", category="climate")
    assert score_climate == 8.5


def test_source_coverage_logarithmic_scaling():
    assert calculate_source_coverage_score(0) == 0.0
    assert calculate_source_coverage_score(1) == 3.32
    assert calculate_source_coverage_score(2) == 5.27
    assert calculate_source_coverage_score(3) == 6.64
    assert calculate_source_coverage_score(7) == 9.97
    assert calculate_source_coverage_score(15) == 10.0  # Capped at 10.0


def test_development_velocity_and_decay():
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    # 4 articles within 1 hour -> high velocity
    vel_active = calculate_development_velocity(
        article_count=4,
        first_seen_at=one_hour_ago,
        last_updated_at=now,
        now=now
    )
    assert vel_active >= 8.0

    # 2 articles published 48 hours ago and no recent updates -> decayed velocity
    two_days_ago = now - timedelta(days=2)
    vel_decayed = calculate_development_velocity(
        article_count=2,
        first_seen_at=two_days_ago - timedelta(hours=2),
        last_updated_at=two_days_ago,
        now=now
    )
    assert vel_decayed < 1.5


def test_importance_composite_weights_and_bounds():
    # Test maximum extreme (all 10s)
    max_scores = compute_event_importance(
        human_impact=10.0,
        global_impact=10.0,
        geographic_impact=10.0,
        economic_impact=10.0,
        political_impact=10.0,
        novelty=10.0,
        velocity=10.0,
        source_coverage=10.0
    )
    assert max_scores.importance_score == 10.0

    # Test minimum extreme (all 0s)
    min_scores = compute_event_importance(
        human_impact=0.0,
        global_impact=0.0,
        geographic_impact=0.0,
        economic_impact=0.0,
        political_impact=0.0,
        novelty=0.0,
        velocity=0.0,
        source_coverage=0.0
    )
    assert min_scores.importance_score == 0.0

    # Test realistic scenario
    # Human: 8.0 * 0.25 = 2.0
    # Global: 6.0 * 0.20 = 1.2
    # Geo: 5.0 * 0.15 = 0.75
    # Econ: 4.0 * 0.10 = 0.4
    # Pol: 5.0 * 0.10 = 0.5
    # Novel: 7.0 * 0.10 = 0.7
    # Vel: 6.0 * 0.05 = 0.3
    # Cov: 5.0 * 0.05 = 0.25
    # Sum: 2.0 + 1.2 + 0.75 + 0.4 + 0.5 + 0.7 + 0.3 + 0.25 = 6.10
    realistic = compute_event_importance(
        human_impact=8.0,
        global_impact=6.0,
        geographic_impact=5.0,
        economic_impact=4.0,
        political_impact=5.0,
        novelty=7.0,
        velocity=6.0,
        source_coverage=5.0
    )
    assert realistic.importance_score == 6.10
