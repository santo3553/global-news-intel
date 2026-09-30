"""
Robust Geocoding & Location Disambiguation Layer.
Fulfills Section 13: Never blindly trust LLM-generated coordinates.
Prevents false precision and assigns calibrated location_confidence.
"""

import re
from typing import Optional, Dict, Any, Tuple


class ResolvedLocation:
    def __init__(
        self,
        name: str,
        country: Optional[str] = None,
        admin_region: Optional[str] = None,
        city: Optional[str] = None,
        latitude: float = 0.0,
        longitude: float = 0.0,
        precision: str = "country",  # 'exact', 'city', 'region', 'country', 'global'
        location_confidence: float = 0.70
    ):
        self.name = name
        self.country = country
        self.admin_region = admin_region
        self.city = city
        self.latitude = latitude
        self.longitude = longitude
        self.precision = precision
        self.location_confidence = location_confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "country": self.country,
            "admin_region": self.admin_region,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "precision": self.precision,
            "location_confidence": self.location_confidence
        }


# Comprehensive Offline Gazetteer of verified coordinates
GAZETTEER_CITIES: Dict[str, Dict[str, Any]] = {
    # Japan
    "miyazaki": {"lat": 31.91, "lng": 131.42, "country": "Japan", "region": "Kyushu", "name": "Miyazaki, Kyushu, Japan"},
    "kumamoto": {"lat": 32.80, "lng": 130.71, "country": "Japan", "region": "Kyushu", "name": "Kumamoto, Kyushu, Japan"},
    "fukuoka": {"lat": 33.59, "lng": 130.40, "country": "Japan", "region": "Kyushu", "name": "Fukuoka, Japan"},
    "tokyo": {"lat": 35.68, "lng": 139.76, "country": "Japan", "region": "Kanto", "name": "Tokyo, Japan"},
    "osaka": {"lat": 34.69, "lng": 135.50, "country": "Japan", "region": "Kansai", "name": "Osaka, Japan"},
    "kyoto": {"lat": 35.01, "lng": 135.76, "country": "Japan", "region": "Kansai", "name": "Kyoto, Japan"},
    "sapporo": {"lat": 43.06, "lng": 141.35, "country": "Japan", "region": "Hokkaido", "name": "Sapporo, Japan"},
    "sendai": {"lat": 38.26, "lng": 140.87, "country": "Japan", "region": "Tohoku", "name": "Sendai, Japan"},
    "naha": {"lat": 26.21, "lng": 127.68, "country": "Japan", "region": "Okinawa", "name": "Naha, Okinawa, Japan"},

    # Switzerland & Western Europe
    "geneva": {"lat": 46.20, "lng": 6.14, "country": "Switzerland", "region": "Geneva", "name": "Geneva, Switzerland"},
    "zurich": {"lat": 47.37, "lng": 8.54, "country": "Switzerland", "region": "Zurich", "name": "Zurich, Switzerland"},
    "bern": {"lat": 46.94, "lng": 7.44, "country": "Switzerland", "region": "Bern", "name": "Bern, Switzerland"},
    "paris": {"lat": 48.85, "lng": 2.35, "country": "France", "region": "Ile-de-France", "name": "Paris, France"},
    "berlin": {"lat": 52.52, "lng": 13.40, "country": "Germany", "region": "Berlin", "name": "Berlin, Germany"},
    "london": {"lat": 51.50, "lng": -0.12, "country": "United Kingdom", "region": "England", "name": "London, United Kingdom"},
    "brussels": {"lat": 50.85, "lng": 4.35, "country": "Belgium", "region": "Brussels", "name": "Brussels, Belgium"},
    "amsterdam": {"lat": 52.37, "lng": 4.89, "country": "Netherlands", "region": "North Holland", "name": "Amsterdam, Netherlands"},
    "rome": {"lat": 41.90, "lng": 12.49, "country": "Italy", "region": "Lazio", "name": "Rome, Italy"},
    "madrid": {"lat": 40.41, "lng": -3.70, "country": "Spain", "region": "Madrid", "name": "Madrid, Spain"},
    "vienna": {"lat": 48.20, "lng": 16.37, "country": "Austria", "region": "Vienna", "name": "Vienna, Austria"},

    # Eastern Europe & Baltics
    "riga": {"lat": 56.95, "lng": 24.10, "country": "Latvia", "region": "Vidzeme", "name": "Riga, Latvia"},
    "tallinn": {"lat": 59.43, "lng": 24.75, "country": "Estonia", "region": "Harju", "name": "Tallinn, Estonia"},
    "vilnius": {"lat": 54.68, "lng": 25.28, "country": "Lithuania", "region": "Vilnius", "name": "Vilnius, Lithuania"},
    "kyiv": {"lat": 50.45, "lng": 30.52, "country": "Ukraine", "region": "Kyiv", "name": "Kyiv, Ukraine"},
    "warsaw": {"lat": 52.23, "lng": 21.01, "country": "Poland", "region": "Mazovia", "name": "Warsaw, Poland"},

    # Americas
    "washington": {"lat": 38.89, "lng": -77.03, "country": "United States", "region": "District of Columbia", "name": "Washington D.C., United States"},
    "new york": {"lat": 40.71, "lng": -74.00, "country": "United States", "region": "New York", "name": "New York, United States"},
    "los angeles": {"lat": 34.05, "lng": -118.24, "country": "United States", "region": "California", "name": "Los Angeles, United States"},
    "chicago": {"lat": 41.88, "lng": -87.62, "country": "United States", "region": "Illinois", "name": "Chicago, United States"},
    "houston": {"lat": 29.76, "lng": -95.36, "country": "United States", "region": "Texas", "name": "Houston, United States"},
    "san francisco": {"lat": 37.77, "lng": -122.41, "country": "United States", "region": "California", "name": "San Francisco, United States"},
    "buenos aires": {"lat": -34.60, "lng": -58.38, "country": "Argentina", "region": "Buenos Aires", "name": "Buenos Aires, Argentina"},
    "sao paulo": {"lat": -23.55, "lng": -46.63, "country": "Brazil", "region": "Sao Paulo", "name": "Sao Paulo, Brazil"},
    "rio de janeiro": {"lat": -22.90, "lng": -43.17, "country": "Brazil", "region": "Rio de Janeiro", "name": "Rio de Janeiro, Brazil"},
    "santiago": {"lat": -33.45, "lng": -70.66, "country": "Chile", "region": "Santiago", "name": "Santiago, Chile"},
    "bogota": {"lat": 4.71, "lng": -74.07, "country": "Colombia", "region": "Bogota", "name": "Bogota, Colombia"},
    "ottawa": {"lat": 45.42, "lng": -75.69, "country": "Canada", "region": "Ontario", "name": "Ottawa, Canada"},
    "mexico city": {"lat": 19.43, "lng": -99.13, "country": "Mexico", "region": "CDMX", "name": "Mexico City, Mexico"},

    # Asia & Middle East
    "beijing": {"lat": 39.90, "lng": 116.40, "country": "China", "region": "Beijing", "name": "Beijing, China"},
    "shanghai": {"lat": 31.23, "lng": 121.47, "country": "China", "region": "Shanghai", "name": "Shanghai, China"},
    "new delhi": {"lat": 28.61, "lng": 77.20, "country": "India", "region": "Delhi", "name": "New Delhi, India"},
    "mumbai": {"lat": 19.07, "lng": 72.87, "country": "India", "region": "Maharashtra", "name": "Mumbai, India"},
    "seoul": {"lat": 37.56, "lng": 126.97, "country": "South Korea", "region": "Seoul", "name": "Seoul, South Korea"},
    "singapore": {"lat": 1.35, "lng": 103.81, "country": "Singapore", "region": "Singapore", "name": "Singapore"},
    "bangkok": {"lat": 13.75, "lng": 100.50, "country": "Thailand", "region": "Bangkok", "name": "Bangkok, Thailand"},
    "taipei": {"lat": 25.03, "lng": 121.56, "country": "Taiwan", "region": "Taipei", "name": "Taipei, Taiwan"},
    "jakarta": {"lat": -6.20, "lng": 106.84, "country": "Indonesia", "region": "Jakarta", "name": "Jakarta, Indonesia"},
    "cairo": {"lat": 30.04, "lng": 31.23, "country": "Egypt", "region": "Cairo", "name": "Cairo, Egypt"},
    "riyadh": {"lat": 24.71, "lng": 46.67, "country": "Saudi Arabia", "region": "Riyadh", "name": "Riyadh, Saudi Arabia"},
    "dubai": {"lat": 25.20, "lng": 55.27, "country": "United Arab Emirates", "region": "Dubai", "name": "Dubai, UAE"},
    "doha": {"lat": 25.28, "lng": 51.53, "country": "Qatar", "region": "Doha", "name": "Doha, Qatar"},
    "jerusalem": {"lat": 31.76, "lng": 35.21, "country": "Israel", "region": "Jerusalem", "name": "Jerusalem"},
    "tel aviv": {"lat": 32.08, "lng": 34.78, "country": "Israel", "region": "Tel Aviv", "name": "Tel Aviv, Israel"},
    "ankara": {"lat": 39.93, "lng": 32.85, "country": "Turkey", "region": "Ankara", "name": "Ankara, Turkey"},
    "tehran": {"lat": 35.68, "lng": 51.38, "country": "Iran", "region": "Tehran", "name": "Tehran, Iran"},

    # Africa & Oceania
    "rabat": {"lat": 34.02, "lng": -6.83, "country": "Morocco", "region": "Rabat", "name": "Rabat, Morocco"},
    "ouarzazate": {"lat": 30.93, "lng": -6.93, "country": "Morocco", "region": "Draa-Tafilalet", "name": "Ouarzazate, Morocco"},
    "nairobi": {"lat": -1.29, "lng": 36.82, "country": "Kenya", "region": "Nairobi", "name": "Nairobi, Kenya"},
    "johannesburg": {"lat": -26.20, "lng": 28.04, "country": "South Africa", "region": "Gauteng", "name": "Johannesburg, South Africa"},
    "sydney": {"lat": -33.86, "lng": 151.20, "country": "Australia", "region": "NSW", "name": "Sydney, Australia"},
    "melbourne": {"lat": -37.81, "lng": 144.96, "country": "Australia", "region": "Victoria", "name": "Melbourne, Australia"},
    "auckland": {"lat": -36.84, "lng": 174.76, "country": "New Zealand", "region": "Auckland", "name": "Auckland, New Zealand"}
}

# Regional Centroids (avoids inventing false city precision when only a province/island is mentioned)
GAZETTEER_REGIONS: Dict[str, Dict[str, Any]] = {
    "kyushu": {"lat": 32.80, "lng": 130.80, "country": "Japan", "region": "Kyushu", "name": "Kyushu, Japan"},
    "hokkaido": {"lat": 43.22, "lng": 142.86, "country": "Japan", "region": "Hokkaido", "name": "Hokkaido, Japan"},
    "honshu": {"lat": 36.50, "lng": 138.00, "country": "Japan", "region": "Honshu", "name": "Honshu, Japan"},
    "baltic": {"lat": 57.00, "lng": 24.50, "country": "Latvia", "region": "Baltic Region", "name": "Baltic Region"},
    "scandinavia": {"lat": 62.00, "lng": 15.00, "country": "Sweden", "region": "Scandinavia", "name": "Scandinavia"},
    "crimea": {"lat": 45.30, "lng": 34.40, "country": "Ukraine", "region": "Crimea", "name": "Crimea"},
    "donbas": {"lat": 48.00, "lng": 38.00, "country": "Ukraine", "region": "Donbas", "name": "Donbas, Ukraine"}
}

# Country Centroids (for country-level precision without hallucinated exact points)
GAZETTEER_COUNTRIES: Dict[str, Dict[str, Any]] = {
    "japan": {"lat": 36.20, "lng": 138.25, "country": "Japan", "name": "Japan"},
    "switzerland": {"lat": 46.81, "lng": 8.22, "country": "Switzerland", "name": "Switzerland"},
    "latvia": {"lat": 56.87, "lng": 24.60, "country": "Latvia", "name": "Latvia"},
    "estonia": {"lat": 58.59, "lng": 25.01, "country": "Estonia", "name": "Estonia"},
    "lithuania": {"lat": 55.16, "lng": 23.88, "country": "Lithuania", "name": "Lithuania"},
    "united states": {"lat": 37.09, "lng": -95.71, "country": "United States", "name": "United States"},
    "usa": {"lat": 37.09, "lng": -95.71, "country": "United States", "name": "United States"},
    "argentina": {"lat": -38.41, "lng": -63.61, "country": "Argentina", "name": "Argentina"},
    "brazil": {"lat": -14.23, "lng": -51.92, "country": "Brazil", "name": "Brazil"},
    "germany": {"lat": 51.16, "lng": 10.45, "country": "Germany", "name": "Germany"},
    "france": {"lat": 46.22, "lng": 2.21, "country": "France", "name": "France"},
    "united kingdom": {"lat": 55.37, "lng": -3.43, "country": "United Kingdom", "name": "United Kingdom"},
    "uk": {"lat": 55.37, "lng": -3.43, "country": "United Kingdom", "name": "United Kingdom"},
    "ukraine": {"lat": 48.37, "lng": 31.16, "country": "Ukraine", "name": "Ukraine"},
    "china": {"lat": 35.86, "lng": 104.19, "country": "China", "name": "China"},
    "india": {"lat": 20.59, "lng": 78.96, "country": "India", "name": "India"},
    "morocco": {"lat": 31.79, "lng": -7.09, "country": "Morocco", "name": "Morocco"},
    "south africa": {"lat": -30.55, "lng": 22.93, "country": "South Africa", "name": "South Africa"},
    "australia": {"lat": -25.27, "lng": 133.77, "country": "Australia", "name": "Australia"},
    "canada": {"lat": 56.13, "lng": -106.34, "country": "Canada", "name": "Canada"}
}


class Geocoder:
    """
    Offline-first gazetteer and coordinate validator.
    Ensures that event coordinates are grounded in verified geospatial data,
    computes location_confidence, and protects against false precision.
    """

    def resolve(
        self,
        raw_name: str,
        country_hint: Optional[str] = None,
        text_context: Optional[str] = None,
        llm_lat: Optional[float] = None,
        llm_lng: Optional[float] = None
    ) -> ResolvedLocation:
        search_str = f"{raw_name} {country_hint or ''} {text_context or ''}".lower()

        # 1. Look for specific City match (Highest Precision: 'city', confidence: 0.95+)
        for city_key, city_data in GAZETTEER_CITIES.items():
            pattern = rf"\b{re.escape(city_key)}\b"
            if re.search(pattern, search_str):
                return ResolvedLocation(
                    name=city_data["name"],
                    country=city_data["country"],
                    admin_region=city_data.get("region"),
                    city=city_key.title(),
                    latitude=city_data["lat"],
                    longitude=city_data["lng"],
                    precision="city",
                    location_confidence=0.96
                )

        # 2. Look for Region / Island / Sub-national match ('region', confidence: 0.85)
        for reg_key, reg_data in GAZETTEER_REGIONS.items():
            pattern = rf"\b{re.escape(reg_key)}\b"
            if re.search(pattern, search_str):
                return ResolvedLocation(
                    name=reg_data["name"],
                    country=reg_data["country"],
                    admin_region=reg_data.get("region"),
                    city=None,
                    latitude=reg_data["lat"],
                    longitude=reg_data["lng"],
                    precision="region",
                    location_confidence=0.88
                )

        # 3. Look for Country match (Broad Precision: 'country', confidence: 0.75 - avoids false precision!)
        for c_key, c_data in GAZETTEER_COUNTRIES.items():
            pattern = rf"\b{re.escape(c_key)}\b"
            if re.search(pattern, search_str):
                # If LLM provided valid coordinates reasonably near the country, we can check, otherwise use centroid
                return ResolvedLocation(
                    name=c_data["name"],
                    country=c_data["country"],
                    admin_region=None,
                    city=None,
                    latitude=c_data["lat"],
                    longitude=c_data["lng"],
                    precision="country",
                    location_confidence=0.75
                )

        # 4. Fallback: If LLM provided valid lat/lng and location name
        if llm_lat is not None and llm_lng is not None and -90 <= llm_lat <= 90 and -180 <= llm_lng <= 180:
            return ResolvedLocation(
                name=raw_name or "Unknown Location",
                country=country_hint,
                latitude=llm_lat,
                longitude=llm_lng,
                precision="city" if raw_name else "country",
                location_confidence=0.60  # unverified LLM coordinates receive lower confidence
            )

        # 5. Global / Uncertain Default
        return ResolvedLocation(
            name="Global / Unspecified Location",
            country=None,
            latitude=0.0,
            longitude=0.0,
            precision="global",
            location_confidence=0.30
        )
