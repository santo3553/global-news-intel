import pytest
from datetime import datetime, timezone
from workers.normalization.normalizer import (
    normalize_url,
    clean_text,
    parse_datetime,
    compute_hashes
)


def test_normalize_url_removes_tracking_params():
    raw_url = "https://EXAMPLE.COM/news/story-123/?utm_source=twitter&utm_medium=social&fbclid=IwAR098&ref=main#section2"
    canonical = normalize_url(raw_url)
    assert canonical == "https://example.com/news/story-123"


def test_normalize_url_sorts_legitimate_params():
    raw_url = "https://example.com/search?z=last&a=first&utm_campaign=promo"
    canonical = normalize_url(raw_url)
    assert canonical == "https://example.com/search?a=first&z=last"


def test_normalize_url_trailing_slash():
    assert normalize_url("https://example.com/world/") == "https://example.com/world"
    assert normalize_url("https://example.com/") == "https://example.com/"


def test_clean_text_decodes_entities_and_strips_tags():
    raw_html = "<p>Breaking News: &quot;Major breakthrough&quot; &amp; historic pact signed in Geneva.</p><br/>"
    cleaned = clean_text(raw_html)
    assert cleaned == 'Breaking News: "Major breakthrough" & historic pact signed in Geneva.'


def test_clean_text_removes_boilerplate():
    raw_text = "Nations agreed to climate goals. The post Nations agreed first appeared on News Wire. All rights reserved."
    cleaned = clean_text(raw_text)
    assert "The post" not in cleaned
    assert "All rights reserved" not in cleaned
    assert "Nations agreed to climate goals." in cleaned


def test_parse_datetime_rfc2822():
    rfc_date = "Mon, 14 Sep 2026 14:30:00 +0000"
    dt = parse_datetime(rfc_date)
    assert isinstance(dt, datetime)
    assert dt.year == 2026
    assert dt.month == 9
    assert dt.day == 14
    assert dt.tzinfo is not None


def test_parse_datetime_iso8601():
    iso_date = "2026-09-14T14:30:00Z"
    dt = parse_datetime(iso_date)
    assert dt.year == 2026
    assert dt.hour == 14
    assert dt.tzinfo == timezone.utc


def test_compute_hashes_deterministic():
    title = "Major Earthquake in Japan"
    content = "A magnitude 7.1 earthquake struck Kyushu."
    t_hash1, c_hash1 = compute_hashes(title, content)
    t_hash2, c_hash2 = compute_hashes(title, content)
    assert t_hash1 == t_hash2
    assert c_hash1 == c_hash2
    assert len(t_hash1) == 64
    assert len(c_hash1) == 64
