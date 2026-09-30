import pytest
from ai.providers.factory import get_ai_provider
from ai.schemas.extraction import ExtractedEventData
from workers.embeddings.embedding_engine import cosine_similarity


@pytest.mark.asyncio
async def test_mock_provider_extract_disaster():
    provider = get_ai_provider()
    title = "Magnitude 7.1 earthquake strikes southern Japan off Miyazaki coast"
    body = (
        "A strong 7.1 magnitude tremor shook Kyushu island in southern Japan on Monday. "
        "The Japan Meteorological Agency issued tsunami advisories for coastal prefectures."
    )
    extracted = await provider.extract_event(title, body)

    assert isinstance(extracted, ExtractedEventData)
    assert extracted.category == "natural_disaster"
    assert extracted.subcategory == "earthquake"
    assert extracted.location.country == "Japan"
    assert extracted.severity >= 0.8
    assert extracted.human_impact_estimate >= 7.0
    assert len(extracted.claims) >= 1
    assert any(e.name == "Japan" for e in extracted.entities)


@pytest.mark.asyncio
async def test_mock_provider_extract_politics():
    provider = get_ai_provider()
    title = "Geneva Climate Summit: Historic Clean Energy Accord Ratified"
    body = (
        "Delegates from 142 nations concluded negotiations in Geneva, Switzerland, "
        "ratifying an accelerated treaty on clean energy transition by 2035."
    )
    extracted = await provider.extract_event(title, body)

    assert extracted.category == "politics"
    assert extracted.location.city == "Geneva"
    assert extracted.location.country == "Switzerland"
    assert extracted.global_impact_estimate >= 8.0


@pytest.mark.asyncio
async def test_embedding_generation_and_cosine_similarity():
    provider = get_ai_provider()

    text_earthquake_1 = "Magnitude 7.1 earthquake strikes southern Japan"
    text_earthquake_2 = "Strong tremor and tsunami warnings in Kyushu, Japan"
    text_unrelated = "French bakery wins annual baguette competition in Paris"

    emb1 = await provider.generate_embedding(text_earthquake_1)
    emb2 = await provider.generate_embedding(text_earthquake_2)
    emb3 = await provider.generate_embedding(text_unrelated)

    # 1. Dimensions check
    assert len(emb1) == 384
    assert len(emb2) == 384
    assert len(emb3) == 384

    # 2. Similarity check: related articles must have significantly higher similarity than unrelated
    sim_related = cosine_similarity(emb1, emb2)
    sim_unrelated = cosine_similarity(emb1, emb3)

    assert sim_related > 0.40
    assert sim_related > sim_unrelated
