import re
import html
import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Tuple, Optional


# Tracking parameters commonly found in RSS & web links
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_name", "utm_cid", "utm_reader", "fbclid", "gclid", "dclid",
    "msclkid", "ref", "source", "guce_referrer", "guce_referrer_usqp",
    "mc_cid", "mc_eid", "_hsenc", "_hsmi", "ncid", "ocid", "cmpid"
}


def normalize_url(raw_url: str) -> str:
    """
    Transforms a raw URL into its canonical form:
    - Strips fragment identifiers
    - Lowercases scheme and hostname
    - Removes tracking parameters (utm_*, fbclid, ref, etc.)
    - Alphabetically sorts remaining query parameters
    - Normalizes trailing slashes
    """
    if not raw_url:
        return ""

    raw_url = raw_url.strip()
    try:
        parts = urlsplit(raw_url)
    except Exception:
        return raw_url

    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path

    # Normalize trailing slash (keep root /)
    if path.endswith("/") and len(path) > 1:
        path = path.rstrip("/")

    # Filter and sort query parameters
    query_params = []
    if parts.query:
        for k, v in parse_qsl(parts.query, keep_blank_values=False):
            if k.lower() not in TRACKING_PARAMS:
                query_params.append((k, v))
        query_params.sort(key=lambda x: x[0])

    new_query = urlencode(query_params)
    # Reconstruct without fragment
    return urlunsplit((scheme, netloc, path, new_query, ""))


def clean_text(text: Optional[str], max_length: int = 12000) -> str:
    """
    Sanitizes raw text or HTML:
    - Strips HTML tags
    - Decodes HTML entities (&amp; -> &, &quot; -> ", etc.)
    - Removes common RSS boilerplate/footers
    - Collapses irregular whitespaces
    - Truncates to max_length safely
    """
    if not text:
        return ""

    # Decode HTML entities
    decoded = html.unescape(text)

    # Strip HTML tags
    no_tags = re.sub(r"<[^>]+>", " ", decoded)

    # Remove common feed/syndication boilerplate patterns
    cleaned = re.sub(r"\bThe post\b.*?(?:appeared first on|first appeared on)\b.*?(?:\.|$)", "", no_tags, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bRead more at\b.*?(?:\.|$)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bAll rights reserved\b\.?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"©\s*\d{4}\b", "", cleaned, flags=re.IGNORECASE)

    # Collapse excessive spaces/tabs/newlines
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned).strip()

    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit(" ", 1)[0] + "..."

    return cleaned


def parse_datetime(raw_date: Optional[str]) -> datetime:
    """
    Parses date string into a UTC timezone-aware datetime.
    Supports RFC 2822, ISO 8601, and common date formats.
    """
    if not raw_date:
        return datetime.now(timezone.utc)

    raw_date = raw_date.strip()

    # 1. Try RFC 2822 (standard RSS date format)
    try:
        dt = parsedate_to_datetime(raw_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # 2. Try ISO 8601 (standard Atom date format)
    try:
        # Handle 'Z' suffix
        iso_str = raw_date.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # 3. Common fallback format patterns
    for fmt in [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d"
    ]:
        try:
            dt = datetime.strptime(raw_date, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    # Fallback to current UTC time if unparseable
    return datetime.now(timezone.utc)


def compute_hashes(title: str, content: str) -> Tuple[str, str]:
    """
    Computes deterministic SHA-256 hashes for normalized title and content.
    Used for Level-2 exact deduplication.
    """
    # Normalize strings for hashing (lowercase and single spaces)
    norm_title = re.sub(r"\s+", " ", title.strip().lower())
    norm_content = re.sub(r"\s+", " ", content.strip().lower())

    title_hash = hashlib.sha256(norm_title.encode("utf-8")).hexdigest()
    content_hash = hashlib.sha256(norm_content.encode("utf-8")).hexdigest()

    return title_hash, content_hash
