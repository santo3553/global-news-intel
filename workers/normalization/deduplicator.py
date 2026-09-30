import re
from typing import Set, Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models import Article


def tokenize(text: str) -> Set[str]:
    """Extract lowercased alphanumeric word tokens."""
    tokens = re.findall(r"\b\w{3,}\b", text.lower())
    return set(tokens)


def get_shingles(text: str, k: int = 4) -> Set[str]:
    """Generates k-character shingles from normalized text."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    if len(normalized) < k:
        return {normalized} if normalized else set()
    return {normalized[i:i + k] for i in range(len(normalized) - k + 1)}


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Computes Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 0.0
    return intersection / union


def compute_text_similarity(text_a: str, text_b: str) -> float:
    """
    Computes hybrid similarity combining word token Jaccard and 4-shingle overlap.
    Returns float between 0.0 and 1.0.
    """
    if not text_a or not text_b:
        return 0.0

    # Token similarity (weights vocabulary overlap)
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    token_sim = jaccard_similarity(tokens_a, tokens_b)

    # Shingle similarity (captures phrasing and character sequence similarity)
    shingles_a = get_shingles(text_a, k=4)
    shingles_b = get_shingles(text_b, k=4)
    shingle_sim = jaccard_similarity(shingles_a, shingles_b)

    # Hybrid blend: 50% tokens, 50% shingles
    return round(0.5 * token_sim + 0.5 * shingle_sim, 4)


class DeduplicationResult:
    def __init__(
        self,
        is_duplicate: bool,
        duplicate_type: Optional[str] = None,  # 'exact_url', 'exact_content', 'exact_title', 'syndicated_near_duplicate'
        matched_article_id: Optional[str] = None,
        similarity_score: float = 0.0,
        details: Optional[str] = None
    ):
        self.is_duplicate = is_duplicate
        self.duplicate_type = duplicate_type
        self.matched_article_id = matched_article_id
        self.similarity_score = similarity_score
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_duplicate": self.is_duplicate,
            "duplicate_type": self.duplicate_type,
            "matched_article_id": self.matched_article_id,
            "similarity_score": self.similarity_score,
            "details": self.details
        }


class Deduplicator:
    """
    Multi-level deduplication engine implementing:
    - Level 1: Exact URL & Canonical URL matching
    - Level 2: Exact content hash & title hash matching
    - Level 3: Near-duplicate / syndicated text similarity within a time window
    """

    def __init__(
        self,
        near_duplicate_threshold: float = 0.82,
        time_window_hours: int = 72
    ):
        self.near_duplicate_threshold = near_duplicate_threshold
        self.time_window_hours = time_window_hours

    async def check_duplicate(
        self,
        session: AsyncSession,
        url: str,
        canonical_url: Optional[str],
        title_hash: str,
        content_hash: str,
        title: str,
        cleaned_content: str,
        published_at: Optional[datetime] = None
    ) -> DeduplicationResult:
        # ==========================================
        # LEVEL 1: Exact URL / Canonical URL Check
        # ==========================================
        url_conditions = [Article.url == url]
        if canonical_url:
            url_conditions.extend([Article.url == canonical_url, Article.canonical_url == canonical_url])

        stmt_url = select(Article.id).where(or_(*url_conditions)).limit(1)
        res_url = await session.execute(stmt_url)
        matched_url_id = res_url.scalar_one_or_none()
        if matched_url_id:
            return DeduplicationResult(
                is_duplicate=True,
                duplicate_type="exact_url",
                matched_article_id=matched_url_id,
                similarity_score=1.0,
                details=f"Matches existing article URL or canonical URL ({matched_url_id})"
            )

        # ==========================================
        # LEVEL 2: Exact Content / Title Hash Check
        # ==========================================
        stmt_hash = select(Article.id, Article.content_hash, Article.title_hash).where(
            or_(
                Article.content_hash == content_hash,
                Article.title_hash == title_hash
            )
        ).limit(1)
        res_hash = await session.execute(stmt_hash)
        matched_hash_row = res_hash.first()
        if matched_hash_row:
            matched_id, m_content_hash, m_title_hash = matched_hash_row
            dup_type = "exact_content" if m_content_hash == content_hash else "exact_title"
            return DeduplicationResult(
                is_duplicate=True,
                duplicate_type=dup_type,
                matched_article_id=matched_id,
                similarity_score=1.0,
                details=f"SHA-256 collision on {dup_type} with article {matched_id}"
            )

        # ==========================================
        # LEVEL 3: Near-Duplicate / Syndication Check
        # ==========================================
        # Compare against candidate articles published in the recent time window
        reference_time = published_at or datetime.now(timezone.utc)
        start_window = reference_time - timedelta(hours=self.time_window_hours)
        end_window = reference_time + timedelta(hours=self.time_window_hours)

        stmt_candidates = select(
            Article.id,
            Article.title,
            Article.cleaned_content
        ).where(
            Article.published_at >= start_window,
            Article.published_at <= end_window
        ).limit(100)  # limit candidate pool to avoid unbounded memory

        res_candidates = await session.execute(stmt_candidates)
        candidates = res_candidates.all()

        for cand_id, cand_title, cand_content in candidates:
            # Check title similarity first (fast filter)
            title_sim = compute_text_similarity(title, cand_title)
            if title_sim > 0.88:
                return DeduplicationResult(
                    is_duplicate=True,
                    duplicate_type="syndicated_near_duplicate",
                    matched_article_id=cand_id,
                    similarity_score=title_sim,
                    details=f"Title near-duplicate with similarity {title_sim:.2f} of article {cand_id}"
                )

            # Check body text similarity if both have substantive content
            if cand_content and cleaned_content and len(cand_content) > 100 and len(cleaned_content) > 100:
                body_sim = compute_text_similarity(cleaned_content, cand_content)
                if body_sim >= self.near_duplicate_threshold:
                    return DeduplicationResult(
                        is_duplicate=True,
                        duplicate_type="syndicated_near_duplicate",
                        matched_article_id=cand_id,
                        similarity_score=body_sim,
                        details=f"Body syndicated text match with similarity {body_sim:.2f} of article {cand_id}"
                    )

        # No duplicate found
        return DeduplicationResult(is_duplicate=False)
