import pytest
from workers.ranking.confidence_scorer import (
    compute_multi_source_confidence,
    get_source_reliability,
    SOURCE_RELIABILITY_CATALOG
)


def test_source_reliability_catalog_lookup():
    assert get_source_reliability("reuters.com") == 0.95
    assert get_source_reliability("apnews.com") == 0.95
    assert get_source_reliability("bbc.com") == 0.92
    assert get_source_reliability("unknown-blog.xyz") == 0.75
    # Explicit reliability override
    assert get_source_reliability("any.com", explicit_reliability=0.88) == 0.88


def test_single_source_cap():
    # Even with top wire (Reuters 0.95), single-source cap must enforce C <= 0.65 (Section 18)
    reuters_only = [{
        "domain": "reuters.com",
        "reliability_score": 0.95,
        "country": "GB"
    }]
    res = compute_multi_source_confidence(
        sources_info=reuters_only,
        location_confidence=1.0
    )
    assert res["single_source_capped"] is True
    # 0.85 * 0.65 + 0.15 * 1.0 = 0.5525 + 0.15 = 0.7025 -> round 0.703
    # source_confidence must strictly be <= 0.65
    assert res["source_confidence"] <= 0.65


def test_multi_source_accumulation_and_country_diversity():
    # 3 distinct sources across 3 countries (Reuters GB, AP US, NHK JP)
    diverse_sources = [
        {"domain": "reuters.com", "reliability_score": 0.95, "country": "GB"},
        {"domain": "apnews.com", "reliability_score": 0.95, "country": "US"},
        {"domain": "nhk.or.jp", "reliability_score": 0.92, "country": "JP"}
    ]
    res = compute_multi_source_confidence(
        sources_info=diverse_sources,
        location_confidence=1.0
    )
    assert res["distinct_sources"] == 3
    assert res["distinct_countries"] == 3
    assert res["single_source_capped"] is False
    assert res["confidence_score"] >= 0.95


def test_contradiction_penalty():
    sources = [
        {"domain": "reuters.com", "reliability_score": 0.95, "country": "GB"},
        {"domain": "apnews.com", "reliability_score": 0.95, "country": "US"}
    ]
    # Without contradiction
    res_normal = compute_multi_source_confidence(sources, location_confidence=1.0, contradiction_detected=False)
    # With contradiction detected
    res_conflict = compute_multi_source_confidence(sources, location_confidence=1.0, contradiction_detected=True, conflict_penalty=0.20)

    assert res_conflict["contradiction_penalty_applied"] is True
    assert res_conflict["confidence_score"] < res_normal["confidence_score"]
    assert round(res_normal["confidence_score"] - res_conflict["confidence_score"], 2) == 0.20
