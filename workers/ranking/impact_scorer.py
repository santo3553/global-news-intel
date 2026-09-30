import math
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from apps.api.app.config import settings

logger = logging.getLogger("gni.ranking.impact")


class ImpactScores:
    """
    Holds the 8 distinct impact dimensions for an event.
    Each dimension is in the range [0.0, 10.0].
    """
    def __init__(
        self,
        human_impact: float,
        global_impact: float,
        geographic_impact: float,
        economic_impact: float,
        political_impact: float,
        novelty: float,
        velocity: float,
        source_coverage: float,
        importance_score: float
    ):
        self.human_impact = human_impact
        self.global_impact = global_impact
        self.geographic_impact = geographic_impact
        self.economic_impact = economic_impact
        self.political_impact = political_impact
        self.novelty = novelty
        self.velocity = velocity
        self.source_coverage = source_coverage
        self.importance_score = importance_score

    def to_dict(self) -> Dict[str, float]:
        return {
            "human_impact_score": self.human_impact,
            "global_impact_score": self.global_impact,
            "geographic_impact_score": self.geographic_impact,
            "economic_impact_score": self.economic_impact,
            "political_impact_score": self.political_impact,
            "novelty_score": self.novelty,
            "development_velocity_score": self.velocity,
            "source_coverage_score": self.source_coverage,
            "importance_score": self.importance_score
        }


def calculate_geographic_scope(
    city: Optional[str] = None,
    admin_region: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None
) -> float:
    """
    Estimates geographic impact score [0.0, 10.0] based on administrative resolution.
    - Local / City: 2.5 - 3.5
    - Regional / State: 4.5 - 6.0
    - National: 7.0 - 8.0
    - Multi-national / Global: 8.5 - 10.0
    """
    if category in ("climate", "global_economy", "science"):
        return 8.5

    if not country:
        return 5.0  # Unspecified or international territory

    if city and admin_region:
        # High-resolution local incident
        return 3.0
    elif city:
        return 3.5
    elif admin_region:
        return 5.5
    else:
        # Country-level national scope
        return 7.5


def calculate_source_coverage_score(num_distinct_sources: int) -> float:
    """
    Log-scaled source breadth score [0.0, 10.0].
    1 source  -> 3.32
    2 sources -> 5.26
    3 sources -> 6.64
    5 sources -> 8.58
    7+ sources -> 10.0
    """
    if num_distinct_sources <= 0:
        return 0.0
    score = 3.3219 * math.log2(1 + num_distinct_sources)
    return round(min(10.0, max(0.0, score)), 2)


def calculate_development_velocity(
    article_count: int,
    first_seen_at: datetime,
    last_updated_at: datetime,
    now: Optional[datetime] = None
) -> float:
    """
    Computes development velocity [0.0, 10.0] based on publication rate and recency decay.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if first_seen_at.tzinfo is None:
        first_seen_at = first_seen_at.replace(tzinfo=timezone.utc)
    if last_updated_at.tzinfo is None:
        last_updated_at = last_updated_at.replace(tzinfo=timezone.utc)

    # Total duration of the event so far
    duration_hours = max(0.25, (last_updated_at - first_seen_at).total_seconds() / 3600.0)
    rate_per_hour = article_count / duration_hours

    # Base velocity scaled to 0-10
    base_velocity = min(10.0, rate_per_hour * 2.5)

    # Recency decay based on time elapsed since last update
    hours_since_last_update = max(0.0, (now - last_updated_at).total_seconds() / 3600.0)
    recency_factor = math.exp(-0.69315 * (hours_since_last_update / 24.0))  # 24h half-life

    velocity = base_velocity * recency_factor
    return round(min(10.0, max(0.0, velocity)), 2)


def compute_event_importance(
    human_impact: float,
    global_impact: float,
    geographic_impact: float,
    economic_impact: float,
    political_impact: float,
    novelty: float,
    velocity: float,
    source_coverage: float
) -> ImpactScores:
    """
    Computes the multi-dimensional weighted importance score according to Section 16:
    Importance = 0.25*Human + 0.20*Global + 0.15*Geo + 0.10*Econ + 0.10*Pol + 0.10*Novelty + 0.05*Velocity + 0.05*Coverage
    """
    # Clamp all inputs to [0.0, 10.0]
    h = max(0.0, min(10.0, human_impact))
    g = max(0.0, min(10.0, global_impact))
    geo = max(0.0, min(10.0, geographic_impact))
    econ = max(0.0, min(10.0, economic_impact))
    pol = max(0.0, min(10.0, political_impact))
    nov = max(0.0, min(10.0, novelty))
    vel = max(0.0, min(10.0, velocity))
    cov = max(0.0, min(10.0, source_coverage))

    composite = (
        settings.IMPORTANCE_HUMAN_WEIGHT * h +
        settings.IMPORTANCE_GLOBAL_WEIGHT * g +
        settings.IMPORTANCE_GEOGRAPHIC_WEIGHT * geo +
        settings.IMPORTANCE_ECONOMIC_WEIGHT * econ +
        settings.IMPORTANCE_POLITICAL_WEIGHT * pol +
        settings.IMPORTANCE_NOVELTY_WEIGHT * nov +
        settings.IMPORTANCE_VELOCITY_WEIGHT * vel +
        settings.IMPORTANCE_SOURCE_COVERAGE_WEIGHT * cov
    )

    importance = round(min(10.0, max(0.0, composite)), 2)

    return ImpactScores(
        human_impact=round(h, 2),
        global_impact=round(g, 2),
        geographic_impact=round(geo, 2),
        economic_impact=round(econ, 2),
        political_impact=round(pol, 2),
        novelty=round(nov, 2),
        velocity=round(vel, 2),
        source_coverage=round(cov, 2),
        importance_score=importance
    )
