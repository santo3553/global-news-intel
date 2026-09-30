import pytest
from workers.extraction.geocoder import Geocoder


def test_geocoder_city_precision():
    geocoder = Geocoder()

    res = geocoder.resolve(
        raw_name="Miyazaki, Japan",
        country_hint="Japan",
        text_context="A tremor was felt in Miyazaki prefecture."
    )

    assert res.city == "Miyazaki"
    assert res.country == "Japan"
    assert res.precision == "city"
    assert res.location_confidence >= 0.95
    assert round(res.latitude, 1) == 31.9
    assert round(res.longitude, 1) == 131.4


def test_geocoder_region_precision():
    geocoder = Geocoder()

    # Article specifies Kyushu region without an exact city
    res = geocoder.resolve(
        raw_name="Kyushu",
        country_hint="Japan",
        text_context="Tremors observed across Kyushu island."
    )

    assert res.precision == "region"
    assert res.city is None
    assert res.country == "Japan"
    assert res.location_confidence >= 0.85
    assert round(res.latitude, 1) == 32.8


def test_geocoder_prevents_false_precision():
    geocoder = Geocoder()

    # Article only mentions country ("Japan")
    res = geocoder.resolve(
        raw_name="Japan",
        country_hint="Japan",
        text_context="Authorities in Japan announced nationwide readiness."
    )

    # Must NOT invent an exact city coordinate!
    assert res.precision == "country"
    assert res.city is None
    assert res.admin_region is None
    assert res.location_confidence <= 0.80


def test_geocoder_unknown_fallback():
    geocoder = Geocoder()

    res = geocoder.resolve(
        raw_name="Unnamed high-seas location",
        text_context="Vessel observed in international waters."
    )

    assert res.precision == "global"
    assert res.location_confidence <= 0.40
