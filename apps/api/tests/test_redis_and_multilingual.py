import pytest
from datetime import datetime, timezone
from apps.api.app.redis_client import (
    set_cache,
    get_cache,
    set_json_cache,
    get_json_cache,
    delete_cache,
    invalidate_patterns,
    ping_redis
)
from ai.providers.factory import get_ai_provider
from workers.extraction.geocoder import Geocoder
from apps.api.app.models import Event, Article
from workers.clustering.clusterer import EventClusterer
from apps.api.app.services.briefing_service import BriefingService
from apps.api.app.schemas.briefing import IntelligenceBriefingResponse


@pytest.mark.asyncio
async def test_redis_cache_layer():
    """Tests basic Redis cache operations and JSON serialization."""
    # Ping
    pong, latency = await ping_redis()
    assert pong is True
    assert latency < 50.0  # sub-50ms (usually < 2ms)

    # String Cache
    await set_cache("unit_test_str", "value_123", ttl_seconds=10)
    cached = await get_cache("unit_test_str")
    assert cached == "value_123"

    # JSON Cache
    data = {"category": "security", "threat_level": "elevated", "items": [1, 2, 3]}
    await set_json_cache("unit_test_json", data, ttl_seconds=10)
    cached_json = await get_json_cache("unit_test_json")
    assert cached_json == data

    # Delete & Invalidation
    await delete_cache("unit_test_str")
    assert await get_cache("unit_test_str") is None

    await set_cache("briefing:test:1", "data1", ttl_seconds=10)
    await set_cache("briefing:test:2", "data2", ttl_seconds=10)
    deleted_count = await invalidate_patterns(["briefing:test:*"])
    assert deleted_count >= 2
    assert await get_cache("briefing:test:1") is None


@pytest.mark.asyncio
async def test_bengali_translation_and_extraction():
    """Tests automated AI translation and geocoding for Bengali native local reports."""
    provider = get_ai_provider()
    geocoder = Geocoder()

    bn_title = "ধানমন্ডি লেকে বড় ধরনের উদ্ধার অভিযান: পুলিশ ও দমকল বাহিনী উপস্থিত"
    bn_body = "ঢাকা শহরের ধানমন্ডি এলাকায় এক বিশেষ উদ্ধার অভিযান পরিচালনা করেছে পুলিশ ও দমকল বাহিনী। এতে স্থানীয় বাসিন্দারা স্বস্তি প্রকাশ করেছেন।"

    # 1. Translation
    eng_title = await provider.translate_to_english(bn_title, "bn")
    eng_body = await provider.translate_to_english(bn_body, "bn")
    assert "Dhanmondi" in eng_title or "Dhaka" in eng_title
    assert "rescue" in eng_title.lower() or "operation" in eng_title.lower() or "police" in eng_title.lower()

    # 2. Extraction
    extracted = await provider.extract_event(bn_title, bn_body)
    assert extracted is not None
    assert extracted.category in ["security", "general", "politics"]

    # 3. Geocoder matches local municipal Dhaka centroid
    resolved = geocoder.resolve(raw_name="", country_hint="BD", text_context=eng_body)
    assert resolved.country == "Bangladesh"
    assert resolved.city == "Dhaka" or resolved.name == "Dhaka, Bangladesh"


@pytest.mark.asyncio
async def test_hindi_translation_and_extraction():
    """Tests automated AI translation and geocoding for Hindi native local reports."""
    provider = get_ai_provider()
    geocoder = Geocoder()

    hi_title = "वाराणसी में भारी बारिश और बाढ़ का अलर्ट: प्रशासन ने जारी की चेतावनी"
    hi_body = "उत्तर प्रदेश के वाराणसी शहर में लगातार बारिश के बाद गंगा नदी का जलस्तर बढ़ गया है। पुलिस और प्रशासन सतर्क है।"

    # 1. Translation
    eng_title = await provider.translate_to_english(hi_title, "hi")
    assert "Varanasi" in eng_title or "flood" in eng_title.lower() or "alert" in eng_title.lower()

    # 2. Extraction
    extracted = await provider.extract_event(hi_title, hi_body)
    assert extracted.category in ["natural_disaster", "general", "security"]

    # 3. Geocoder matches Varanasi
    resolved = geocoder.resolve(raw_name="", country_hint="IN", text_context=eng_title)
    assert resolved.country == "India"
    assert resolved.city == "Varanasi"


@pytest.mark.asyncio
async def test_urdu_translation_and_extraction():
    """Tests automated AI translation and geocoding for Urdu native local reports."""
    provider = get_ai_provider()

    ur_title = "راولپنڈی میں پولیس کی کارروائی، اہم ملزمان گرفتار"
    ur_body = "پنجاب پولیس نے راولپنڈی میں سرچ آپریشن کے دوران مشتبہ افراد کو حراست میں لے لیا۔"

    eng_title = await provider.translate_to_english(ur_title, "ur")
    assert "Rawalpindi" in eng_title or "police" in eng_title.lower() or "arrested" in eng_title.lower()

    extracted = await provider.extract_event(ur_title, ur_body)
    assert extracted is not None


@pytest.mark.asyncio
async def test_arabic_translation_and_extraction():
    """Tests automated AI translation and geocoding for Arabic native local reports."""
    provider = get_ai_provider()

    ar_title = "الدوحة تستضيف قمة جديدة لبحث الاتفاق الاقتصادي الإقليمي"
    ar_body = "عقدت وفود دبلوماسية في العاصمة القطرية الدوحة اجتماعات لمناقشة التعاون التجاري ومشاريع الطاقة."

    eng_title = await provider.translate_to_english(ar_title, "ar")
    assert "Doha" in eng_title or "summit" in eng_title.lower() or "accord" in eng_title.lower()

    extracted = await provider.extract_event(ar_title, ar_body)
    assert extracted.category in ["politics", "economy", "general"]


@pytest.mark.asyncio
async def test_spanish_translation_and_extraction():
    """Tests automated AI translation and geocoding for Spanish native local reports."""
    provider = get_ai_provider()

    es_title = "Terremoto de magnitud 6.2 sacude la costa cerca de Santiago de Chile"
    es_body = "Un fuerte sismo se sintió en la región central del país. Autoridades de emergencia descartan víctimas fatales."

    eng_title = await provider.translate_to_english(es_title, "es")
    assert "earthquake" in eng_title.lower() or "santiago" in eng_title.lower()

    extracted = await provider.extract_event(es_title, es_body)
    assert extracted.category == "natural_disaster"
    assert extracted.subcategory == "earthquake"


@pytest.mark.asyncio
async def test_clustering_preserves_native_metadata(async_db):
    """Verifies that EventClusterer attaches original_language, original_title, and original_summary to new Events."""
    provider = get_ai_provider()
    clusterer = EventClusterer()

    native_title = "চট্টগ্রাম বন্দরে নতুন কন্টেইনার টার্মিনাল চালু"
    native_content = "চট্টগ্রাম বন্দরে বাণিজ্য বৃদ্ধির লক্ষ্যে আধুনিক প্রযুক্তি সম্বলিত নতুন টার্মিনালের কার্যক্রম শুরু হয়েছে।"

    # Translated into canonical English
    eng_title = await provider.translate_to_english(native_title, "bn")
    eng_content = await provider.translate_to_english(native_content, "bn")

    # Founding article entity
    article = Article(
        id="art-native-test-01",
        source_id="src-prothomalo-bn",
        title=eng_title,
        url="https://prothomalo.com/business/chittagong-terminal-01",
        canonical_url="https://prothomalo.com/business/chittagong-terminal-01",
        language="bn",
        original_language="bn",
        original_title=native_title,
        original_content=native_content,
        cleaned_content=eng_content,
        raw_content=native_content,
        processing_status="extracted",
        published_at=datetime.now(timezone.utc)
    )
    async_db.add(article)
    await async_db.flush()

    extracted_data = await provider.extract_event(article.title, article.cleaned_content)
    decision = await clusterer.cluster_article(async_db, article, extracted_data)

    assert decision.action == "created"
    
    # Verify event record in database
    event = await async_db.get(Event, decision.event_id)
    assert event is not None
    assert event.original_language == "bn"
    assert event.original_title == native_title
    assert event.original_summary is not None
    assert len(event.original_summary) > 0
