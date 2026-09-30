import logging
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger("gni.ranking.confidence")

# Standard reliability priors by recognized domain (Section 17)
SOURCE_RELIABILITY_CATALOG: Dict[str, float] = {
    "reuters.com": 0.95,
    "apnews.com": 0.95,
    "afp.com": 0.95,
    "bbc.com": 0.92,
    "nhk.or.jp": 0.92,
    "dw.com": 0.90,
    "france24.com": 0.88,
    "theguardian.com": 0.88,
    "aljazeera.com": 0.85,
    "euronews.com": 0.85,
    "scmp.com": 0.82,
    "nikkei.com": 0.85,
    "japantimes.co.jp": 0.84,
}

DEFAULT_RELIABILITY = 0.75


def get_source_reliability(domain: Optional[str] = None, explicit_reliability: Optional[float] = None) -> float:
    """
    Returns source reliability prior.
    """
    if explicit_reliability is not None and explicit_reliability > 0:
        return max(0.10, min(1.0, explicit_reliability))
    if domain:
        clean_domain = domain.lower().strip()
        for known_domain, score in SOURCE_RELIABILITY_CATALOG.items():
            if known_domain in clean_domain:
                return score
    return DEFAULT_RELIABILITY


def compute_multi_source_confidence(
    sources_info: List[Dict[str, Any]],
    location_confidence: float = 1.0,
    contradiction_detected: bool = False,
    conflict_penalty: float = 0.15
) -> Dict[str, Any]:
    """
    Computes rigorous event confidence score according to Section 18:
    1. Independent sources accumulation: C_base = 1 - prod(1 - R_s)
    2. Single-source cap: C <= 0.65 for 1 source
    3. Dual-source cap: C <= 0.85 for 2 sources
    4. Multi-source cap: C <= 0.98 for 3+ sources across distinct domains/countries
    5. Location precision weighting (0.85*C_source + 0.15*C_loc)
    6. Contradiction penalty if conflicting claims exist
    """
    if not sources_info:
        return {
            "confidence_score": 0.40,
            "distinct_sources": 0,
            "distinct_countries": 0,
            "single_source_capped": False,
            "contradiction_penalty_applied": False
        }

    # Group by unique source identifier or domain to prevent single-outlet inflation
    unique_sources: Dict[str, Dict[str, Any]] = {}
    distinct_countries: Set[str] = set()

    for s in sources_info:
        key = (s.get("domain") or s.get("source_id") or s.get("source_name") or "unknown").lower().strip()
        if key not in unique_sources:
            unique_sources[key] = s
            country = s.get("country")
            if country:
                distinct_countries.add(country.upper().strip())

    num_distinct = len(unique_sources)

    # 1. Base Multi-Source Probability Accumulation
    # C_base = 1 - prod(1 - R_i)
    unreliability_product = 1.0
    for s in unique_sources.values():
        r = get_source_reliability(s.get("domain"), s.get("reliability_score"))
        unreliability_product *= (1.0 - r)

    c_sources = 1.0 - unreliability_product

    # 2. Strict Single & Dual Source Caps (Section 18)
    single_source_capped = False
    if num_distinct == 1:
        if c_sources > 0.65:
            c_sources = 0.65
            single_source_capped = True
    elif num_distinct == 2:
        c_sources = min(0.85, c_sources)
    else:
        # 3 or more distinct sources
        if len(distinct_countries) >= 2:
            c_sources = min(0.98, c_sources)
        else:
            c_sources = min(0.92, c_sources)

    # 3. Location Precision Factor (15% weight)
    loc_factor = max(0.0, min(1.0, location_confidence))
    c_combined = (0.85 * c_sources) + (0.15 * loc_factor)

    # 4. Contradiction Penalty
    contradiction_applied = False
    if contradiction_detected:
        c_combined -= conflict_penalty
        contradiction_applied = True

    final_confidence = round(max(0.10, min(0.99, c_combined)), 3)

    return {
        "confidence_score": final_confidence,
        "distinct_sources": num_distinct,
        "distinct_countries": len(distinct_countries),
        "source_confidence": round(c_sources, 3),
        "location_confidence": round(loc_factor, 3),
        "single_source_capped": single_source_capped,
        "contradiction_penalty_applied": contradiction_applied
    }
