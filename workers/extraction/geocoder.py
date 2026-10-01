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
    "hiroshima": {"lat": 34.38, "lng": 132.45, "country": "Japan", "region": "Chugoku", "name": "Hiroshima, Japan"},

    # Switzerland & Western Europe
    "geneva": {"lat": 46.20, "lng": 6.14, "country": "Switzerland", "region": "Geneva", "name": "Geneva, Switzerland"},
    "zurich": {"lat": 47.37, "lng": 8.54, "country": "Switzerland", "region": "Zurich", "name": "Zurich, Switzerland"},
    "bern": {"lat": 46.94, "lng": 7.44, "country": "Switzerland", "region": "Bern", "name": "Bern, Switzerland"},
    "paris": {"lat": 48.85, "lng": 2.35, "country": "France", "region": "Ile-de-France", "name": "Paris, France"},
    "marseille": {"lat": 43.29, "lng": 5.37, "country": "France", "region": "PACA", "name": "Marseille, France"},
    "berlin": {"lat": 52.52, "lng": 13.40, "country": "Germany", "region": "Berlin", "name": "Berlin, Germany"},
    "munich": {"lat": 48.13, "lng": 11.58, "country": "Germany", "region": "Bavaria", "name": "Munich, Germany"},
    "frankfurt": {"lat": 50.11, "lng": 8.68, "country": "Germany", "region": "Hesse", "name": "Frankfurt, Germany"},
    "london": {"lat": 51.50, "lng": -0.12, "country": "United Kingdom", "region": "England", "name": "London, United Kingdom"},
    "edinburgh": {"lat": 55.95, "lng": -3.18, "country": "United Kingdom", "region": "Scotland", "name": "Edinburgh, United Kingdom"},
    "brussels": {"lat": 50.85, "lng": 4.35, "country": "Belgium", "region": "Brussels", "name": "Brussels, Belgium"},
    "amsterdam": {"lat": 52.37, "lng": 4.89, "country": "Netherlands", "region": "North Holland", "name": "Amsterdam, Netherlands"},
    "the hague": {"lat": 52.07, "lng": 4.30, "country": "Netherlands", "region": "South Holland", "name": "The Hague, Netherlands"},
    "rome": {"lat": 41.90, "lng": 12.49, "country": "Italy", "region": "Lazio", "name": "Rome, Italy"},
    "milan": {"lat": 45.46, "lng": 9.19, "country": "Italy", "region": "Lombardy", "name": "Milan, Italy"},
    "madrid": {"lat": 40.41, "lng": -3.70, "country": "Spain", "region": "Madrid", "name": "Madrid, Spain"},
    "barcelona": {"lat": 41.38, "lng": 2.17, "country": "Spain", "region": "Catalonia", "name": "Barcelona, Spain"},
    "vienna": {"lat": 48.20, "lng": 16.37, "country": "Austria", "region": "Vienna", "name": "Vienna, Austria"},
    "athens": {"lat": 37.98, "lng": 23.72, "country": "Greece", "region": "Attica", "name": "Athens, Greece"},
    "stockholm": {"lat": 59.32, "lng": 18.06, "country": "Sweden", "region": "Stockholm", "name": "Stockholm, Sweden"},
    "oslo": {"lat": 59.91, "lng": 10.75, "country": "Norway", "region": "Oslo", "name": "Oslo, Norway"},
    "copenhagen": {"lat": 55.67, "lng": 12.56, "country": "Denmark", "region": "Capital", "name": "Copenhagen, Denmark"},
    "helsinki": {"lat": 60.16, "lng": 24.93, "country": "Finland", "region": "Uusimaa", "name": "Helsinki, Finland"},
    "reykjavik": {"lat": 64.14, "lng": -21.94, "country": "Iceland", "region": "Capital", "name": "Reykjavik, Iceland"},
    "grindavik": {"lat": 63.84, "lng": -22.43, "country": "Iceland", "region": "Southern Peninsula", "name": "Grindavik, Iceland"},
    "dublin": {"lat": 53.34, "lng": -6.26, "country": "Ireland", "region": "Leinster", "name": "Dublin, Ireland"},
    "lisbon": {"lat": 38.72, "lng": -9.13, "country": "Portugal", "region": "Lisbon", "name": "Lisbon, Portugal"},

    # Eastern Europe, Baltics & Russia
    "riga": {"lat": 56.95, "lng": 24.10, "country": "Latvia", "region": "Vidzeme", "name": "Riga, Latvia"},
    "tallinn": {"lat": 59.43, "lng": 24.75, "country": "Estonia", "region": "Harju", "name": "Tallinn, Estonia"},
    "vilnius": {"lat": 54.68, "lng": 25.28, "country": "Lithuania", "region": "Vilnius", "name": "Vilnius, Lithuania"},
    "kyiv": {"lat": 50.45, "lng": 30.52, "country": "Ukraine", "region": "Kyiv", "name": "Kyiv, Ukraine"},
    "kharkiv": {"lat": 49.99, "lng": 36.23, "country": "Ukraine", "region": "Kharkiv", "name": "Kharkiv, Ukraine"},
    "odesa": {"lat": 46.48, "lng": 30.72, "country": "Ukraine", "region": "Odesa", "name": "Odesa, Ukraine"},
    "zaporizhzhia": {"lat": 47.83, "lng": 35.13, "country": "Ukraine", "region": "Zaporizhzhia", "name": "Zaporizhzhia, Ukraine"},
    "lviv": {"lat": 49.83, "lng": 24.02, "country": "Ukraine", "region": "Lviv", "name": "Lviv, Ukraine"},
    "sevastopol": {"lat": 44.61, "lng": 33.52, "country": "Ukraine", "region": "Crimea", "name": "Sevastopol, Crimea"},
    "warsaw": {"lat": 52.23, "lng": 21.01, "country": "Poland", "region": "Mazovia", "name": "Warsaw, Poland"},
    "krakow": {"lat": 50.06, "lng": 19.94, "country": "Poland", "region": "Lesser Poland", "name": "Krakow, Poland"},
    "prague": {"lat": 50.07, "lng": 14.43, "country": "Czech Republic", "region": "Prague", "name": "Prague, Czechia"},
    "budapest": {"lat": 47.49, "lng": 19.04, "country": "Hungary", "region": "Central Hungary", "name": "Budapest, Hungary"},
    "bucharest": {"lat": 44.42, "lng": 26.10, "country": "Romania", "region": "Bucharest", "name": "Bucharest, Romania"},
    "moscow": {"lat": 55.75, "lng": 37.61, "country": "Russia", "region": "Moscow", "name": "Moscow, Russia"},
    "saint petersburg": {"lat": 59.93, "lng": 30.33, "country": "Russia", "region": "Saint Petersburg", "name": "St. Petersburg, Russia"},
    "belgorod": {"lat": 50.59, "lng": 36.58, "country": "Russia", "region": "Belgorod", "name": "Belgorod, Russia"},

    # Americas
    "washington": {"lat": 38.89, "lng": -77.03, "country": "United States", "region": "District of Columbia", "name": "Washington D.C., United States"},
    "new york": {"lat": 40.71, "lng": -74.00, "country": "United States", "region": "New York", "name": "New York, United States"},
    "baltimore": {"lat": 39.29, "lng": -76.61, "country": "United States", "region": "Maryland", "name": "Baltimore, Maryland, United States"},
    "boston": {"lat": 42.36, "lng": -71.05, "country": "United States", "region": "Massachusetts", "name": "Boston, Massachusetts, United States"},
    "los angeles": {"lat": 34.05, "lng": -118.24, "country": "United States", "region": "California", "name": "Los Angeles, United States"},
    "chicago": {"lat": 41.88, "lng": -87.62, "country": "United States", "region": "Illinois", "name": "Chicago, United States"},
    "houston": {"lat": 29.76, "lng": -95.36, "country": "United States", "region": "Texas", "name": "Houston, United States"},
    "miami": {"lat": 25.76, "lng": -80.19, "country": "United States", "region": "Florida", "name": "Miami, Florida, United States"},
    "seattle": {"lat": 47.60, "lng": -122.33, "country": "United States", "region": "Washington", "name": "Seattle, Washington, United States"},
    "san francisco": {"lat": 37.77, "lng": -122.41, "country": "United States", "region": "California", "name": "San Francisco, United States"},
    "honolulu": {"lat": 21.30, "lng": -157.85, "country": "United States", "region": "Hawaii", "name": "Honolulu, Hawaii, United States"},
    "anchorage": {"lat": 61.21, "lng": -149.90, "country": "United States", "region": "Alaska", "name": "Anchorage, Alaska, United States"},
    "ottawa": {"lat": 45.42, "lng": -75.69, "country": "Canada", "region": "Ontario", "name": "Ottawa, Canada"},
    "toronto": {"lat": 43.65, "lng": -79.38, "country": "Canada", "region": "Ontario", "name": "Toronto, Canada"},
    "vancouver": {"lat": 49.28, "lng": -123.12, "country": "Canada", "region": "British Columbia", "name": "Vancouver, Canada"},
    "mexico city": {"lat": 19.43, "lng": -99.13, "country": "Mexico", "region": "CDMX", "name": "Mexico City, Mexico"},
    "havana": {"lat": 23.11, "lng": -82.36, "country": "Cuba", "region": "Havana", "name": "Havana, Cuba"},
    "panama city": {"lat": 8.98, "lng": -79.51, "country": "Panama", "region": "Panama", "name": "Panama City, Panama"},
    "bogota": {"lat": 4.71, "lng": -74.07, "country": "Colombia", "region": "Bogota", "name": "Bogota, Colombia"},
    "caracas": {"lat": 10.48, "lng": -66.90, "country": "Venezuela", "region": "Capital", "name": "Caracas, Venezuela"},
    "lima": {"lat": -12.04, "lng": -77.04, "country": "Peru", "region": "Lima", "name": "Lima, Peru"},
    "santiago": {"lat": -33.45, "lng": -70.66, "country": "Chile", "region": "Santiago", "name": "Santiago, Chile"},
    "buenos aires": {"lat": -34.60, "lng": -58.38, "country": "Argentina", "region": "Buenos Aires", "name": "Buenos Aires, Argentina"},
    "sao paulo": {"lat": -23.55, "lng": -46.63, "country": "Brazil", "region": "Sao Paulo", "name": "Sao Paulo, Brazil"},
    "rio de janeiro": {"lat": -22.90, "lng": -43.17, "country": "Brazil", "region": "Rio de Janeiro", "name": "Rio de Janeiro, Brazil"},
    "brasilia": {"lat": -15.79, "lng": -47.88, "country": "Brazil", "region": "Federal District", "name": "Brasilia, Brazil"},

    # Middle East & Levant
    "gaza": {"lat": 31.50, "lng": 34.46, "country": "Palestine", "region": "Gaza Strip", "name": "Gaza City, Gaza Strip"},
    "rafah": {"lat": 31.29, "lng": 34.25, "country": "Palestine", "region": "Gaza Strip", "name": "Rafah, Gaza Strip"},
    "khan younis": {"lat": 31.34, "lng": 34.30, "country": "Palestine", "region": "Gaza Strip", "name": "Khan Younis, Gaza Strip"},
    "beirut": {"lat": 33.89, "lng": 35.50, "country": "Lebanon", "region": "Beirut", "name": "Beirut, Lebanon"},
    "damascus": {"lat": 33.51, "lng": 36.27, "country": "Syria", "region": "Damascus", "name": "Damascus, Syria"},
    "baghdad": {"lat": 33.31, "lng": 44.36, "country": "Iraq", "region": "Baghdad", "name": "Baghdad, Iraq"},
    "erbil": {"lat": 36.19, "lng": 44.01, "country": "Iraq", "region": "Kurdistan", "name": "Erbil, Iraq"},
    "sanaa": {"lat": 15.36, "lng": 44.19, "country": "Yemen", "region": "Sanaa", "name": "Sanaa, Yemen"},
    "hodeidah": {"lat": 14.79, "lng": 42.95, "country": "Yemen", "region": "Al Hudaydah", "name": "Hodeidah, Yemen"},
    "aden": {"lat": 12.78, "lng": 45.01, "country": "Yemen", "region": "Aden", "name": "Aden, Yemen"},
    "tehran": {"lat": 35.68, "lng": 51.38, "country": "Iran", "region": "Tehran", "name": "Tehran, Iran"},
    "isfahan": {"lat": 32.65, "lng": 51.66, "country": "Iran", "region": "Isfahan", "name": "Isfahan, Iran"},
    "jerusalem": {"lat": 31.76, "lng": 35.21, "country": "Israel", "region": "Jerusalem", "name": "Jerusalem"},
    "tel aviv": {"lat": 32.08, "lng": 34.78, "country": "Israel", "region": "Tel Aviv", "name": "Tel Aviv, Israel"},
    "riyadh": {"lat": 24.71, "lng": 46.67, "country": "Saudi Arabia", "region": "Riyadh", "name": "Riyadh, Saudi Arabia"},
    "dubai": {"lat": 25.20, "lng": 55.27, "country": "United Arab Emirates", "region": "Dubai", "name": "Dubai, UAE"},
    "doha": {"lat": 25.28, "lng": 51.53, "country": "Qatar", "region": "Doha", "name": "Doha, Qatar"},
    "kuwait": {"lat": 29.37, "lng": 47.97, "country": "Kuwait", "region": "Capital", "name": "Kuwait City, Kuwait"},
    "amman": {"lat": 31.94, "lng": 35.92, "country": "Jordan", "region": "Amman", "name": "Amman, Jordan"},
    "ankara": {"lat": 39.93, "lng": 32.85, "country": "Turkey", "region": "Ankara", "name": "Ankara, Turkey"},
    "istanbul": {"lat": 41.00, "lng": 28.97, "country": "Turkey", "region": "Marmara", "name": "Istanbul, Turkey"},

    # Strategic Maritime Chokepoints (Precision: maritime)
    "strait of hormuz": {"lat": 26.56, "lng": 56.25, "country": "Oman/Iran", "region": "Persian Gulf", "name": "Strait of Hormuz (Oil Transit Chokepoint)"},
    "bab el-mandeb": {"lat": 12.58, "lng": 43.33, "country": "Yemen/Djibouti", "region": "Red Sea", "name": "Bab el-Mandeb (Red Sea Corridor)"},
    "suez canal": {"lat": 30.58, "lng": 32.57, "country": "Egypt", "region": "Suez", "name": "Suez Canal Maritime Arterial"},
    "panama canal": {"lat": 9.08, "lng": -79.68, "country": "Panama", "region": "Panama", "name": "Panama Canal Transit Corridor"},
    "taiwan strait": {"lat": 24.00, "lng": 119.50, "country": "Taiwan", "region": "East Asia", "name": "Taiwan Strait Geopolitical Corridor"},
    "strait of malacca": {"lat": 2.20, "lng": 102.25, "country": "Malaysia/Indonesia", "region": "Southeast Asia", "name": "Strait of Malacca"},

    # Asia & Indo-Pacific
    "beijing": {"lat": 39.90, "lng": 116.40, "country": "China", "region": "Beijing", "name": "Beijing, China"},
    "shanghai": {"lat": 31.23, "lng": 121.47, "country": "China", "region": "Shanghai", "name": "Shanghai, China"},
    "guangzhou": {"lat": 23.12, "lng": 113.26, "country": "China", "region": "Guangdong", "name": "Guangzhou, China"},
    "shenzhen": {"lat": 22.54, "lng": 114.05, "country": "China", "region": "Guangdong", "name": "Shenzhen, China"},
    "hong kong": {"lat": 22.31, "lng": 114.16, "country": "China", "region": "Hong Kong", "name": "Hong Kong"},
    "taipei": {"lat": 25.03, "lng": 121.56, "country": "Taiwan", "region": "Taipei", "name": "Taipei, Taiwan"},
    "kaohsiung": {"lat": 22.62, "lng": 120.30, "country": "Taiwan", "region": "Kaohsiung", "name": "Kaohsiung, Taiwan"},
    "seoul": {"lat": 37.56, "lng": 126.97, "country": "South Korea", "region": "Seoul", "name": "Seoul, South Korea"},
    "pyongyang": {"lat": 39.03, "lng": 125.76, "country": "North Korea", "region": "Pyongyang", "name": "Pyongyang, North Korea"},
    "new delhi": {"lat": 28.61, "lng": 77.20, "country": "India", "region": "Delhi", "name": "New Delhi, India"},
    "mumbai": {"lat": 19.07, "lng": 72.87, "country": "India", "region": "Maharashtra", "name": "Mumbai, India"},
    "chennai": {"lat": 13.08, "lng": 80.27, "country": "India", "region": "Tamil Nadu", "name": "Chennai, Tamil Nadu, India"},
    "bengaluru": {"lat": 12.97, "lng": 77.59, "country": "India", "region": "Karnataka", "name": "Bengaluru, Karnataka, India"},
    "bangalore": {"lat": 12.97, "lng": 77.59, "country": "India", "region": "Karnataka", "name": "Bengaluru, Karnataka, India"},
    "kolkata": {"lat": 22.57, "lng": 88.36, "country": "India", "region": "West Bengal", "name": "Kolkata, West Bengal, India"},
    "hyderabad": {"lat": 17.38, "lng": 78.48, "country": "India", "region": "Telangana", "name": "Hyderabad, Telangana, India"},
    "islamabad": {"lat": 33.68, "lng": 73.04, "country": "Pakistan", "region": "Islamabad", "name": "Islamabad, Pakistan"},
    "karachi": {"lat": 24.86, "lng": 67.00, "country": "Pakistan", "region": "Sindh", "name": "Karachi, Pakistan"},
    "lahore": {"lat": 31.52, "lng": 74.35, "country": "Pakistan", "region": "Punjab", "name": "Lahore, Pakistan"},
    "dhaka": {"lat": 23.81, "lng": 90.41, "country": "Bangladesh", "region": "Dhaka", "name": "Dhaka, Bangladesh"},
    "chittagong": {"lat": 22.35, "lng": 91.78, "country": "Bangladesh", "region": "Chittagong", "name": "Chittagong, Bangladesh"},
    "colombo": {"lat": 6.92, "lng": 79.86, "country": "Sri Lanka", "region": "Western", "name": "Colombo, Sri Lanka"},
    "kathmandu": {"lat": 27.71, "lng": 85.32, "country": "Nepal", "region": "Bagmati", "name": "Kathmandu, Nepal"},
    "singapore": {"lat": 1.35, "lng": 103.81, "country": "Singapore", "region": "Singapore", "name": "Singapore"},
    "bangkok": {"lat": 13.75, "lng": 100.50, "country": "Thailand", "region": "Bangkok", "name": "Bangkok, Thailand"},
    "chiang mai": {"lat": 18.79, "lng": 98.98, "country": "Thailand", "region": "Chiang Mai", "name": "Chiang Mai, Thailand"},
    "jakarta": {"lat": -6.20, "lng": 106.84, "country": "Indonesia", "region": "Jakarta", "name": "Jakarta, Indonesia"},
    "surabaya": {"lat": -7.25, "lng": 112.75, "country": "Indonesia", "region": "East Java", "name": "Surabaya, Indonesia"},
    "manila": {"lat": 14.59, "lng": 120.98, "country": "Philippines", "region": "Metro Manila", "name": "Manila, Philippines"},
    "cebu": {"lat": 10.31, "lng": 123.88, "country": "Philippines", "region": "Central Visayas", "name": "Cebu City, Philippines"},
    "hanoi": {"lat": 21.02, "lng": 105.83, "country": "Vietnam", "region": "Hanoi", "name": "Hanoi, Vietnam"},
    "ho chi minh city": {"lat": 10.82, "lng": 106.63, "country": "Vietnam", "region": "Southeast", "name": "Ho Chi Minh City, Vietnam"},
    "kuala lumpur": {"lat": 3.13, "lng": 101.68, "country": "Malaysia", "region": "Kuala Lumpur", "name": "Kuala Lumpur, Malaysia"},
    "penang": {"lat": 5.41, "lng": 100.33, "country": "Malaysia", "region": "Penang", "name": "George Town, Penang, Malaysia"},
    "busan": {"lat": 35.17, "lng": 129.07, "country": "South Korea", "region": "Yeongnam", "name": "Busan, South Korea"},

    # Middle East, North Africa & Levant (Local additions)
    "jeddah": {"lat": 21.48, "lng": 39.19, "country": "Saudi Arabia", "region": "Makkah", "name": "Jeddah, Saudi Arabia"},
    "abu dhabi": {"lat": 24.45, "lng": 54.37, "country": "United Arab Emirates", "region": "Abu Dhabi", "name": "Abu Dhabi, UAE"},
    "alexandria": {"lat": 31.20, "lng": 29.91, "country": "Egypt", "region": "Alexandria", "name": "Alexandria, Egypt"},
    "casablanca": {"lat": 33.57, "lng": -7.58, "country": "Morocco", "region": "Casablanca-Settat", "name": "Casablanca, Morocco"},

    # Africa & Oceania
    "cairo": {"lat": 30.04, "lng": 31.23, "country": "Egypt", "region": "Cairo", "name": "Cairo, Egypt"},
    "rabat": {"lat": 34.02, "lng": -6.83, "country": "Morocco", "region": "Rabat", "name": "Rabat, Morocco"},
    "ouarzazate": {"lat": 30.93, "lng": -6.93, "country": "Morocco", "region": "Draa-Tafilalet", "name": "Ouarzazate, Morocco"},
    "tripoli": {"lat": 32.88, "lng": 13.19, "country": "Libya", "region": "Tripoli", "name": "Tripoli, Libya"},
    "khartoum": {"lat": 15.50, "lng": 32.55, "country": "Sudan", "region": "Khartoum", "name": "Khartoum, Sudan"},
    "port sudan": {"lat": 19.61, "lng": 37.21, "country": "Sudan", "region": "Red Sea", "name": "Port Sudan, Sudan"},
    "addis ababa": {"lat": 9.03, "lng": 38.74, "country": "Ethiopia", "region": "Addis Ababa", "name": "Addis Ababa, Ethiopia"},
    "nairobi": {"lat": -1.29, "lng": 36.82, "country": "Kenya", "region": "Nairobi", "name": "Nairobi, Kenya"},
    "mombasa": {"lat": -4.04, "lng": 39.66, "country": "Kenya", "region": "Coast", "name": "Mombasa, Kenya"},
    "accra": {"lat": 5.60, "lng": -0.18, "country": "Ghana", "region": "Greater Accra", "name": "Accra, Ghana"},
    "kinshasa": {"lat": -4.44, "lng": 15.26, "country": "DR Congo", "region": "Kinshasa", "name": "Kinshasa, DR Congo"},
    "lagos": {"lat": 6.52, "lng": 3.37, "country": "Nigeria", "region": "Lagos", "name": "Lagos, Nigeria"},
    "abuja": {"lat": 9.07, "lng": 7.39, "country": "Nigeria", "region": "FCT", "name": "Abuja, Nigeria"},
    "johannesburg": {"lat": -26.20, "lng": 28.04, "country": "South Africa", "region": "Gauteng", "name": "Johannesburg, South Africa"},
    "cape town": {"lat": -33.92, "lng": 18.42, "country": "South Africa", "region": "Western Cape", "name": "Cape Town, South Africa"},
    "durban": {"lat": -29.85, "lng": 31.02, "country": "South Africa", "region": "KwaZulu-Natal", "name": "Durban, South Africa"},
    "sydney": {"lat": -33.86, "lng": 151.20, "country": "Australia", "region": "NSW", "name": "Sydney, Australia"},
    "melbourne": {"lat": -37.81, "lng": 144.96, "country": "Australia", "region": "Victoria", "name": "Melbourne, Australia"},
    "auckland": {"lat": -36.84, "lng": 174.76, "country": "New Zealand", "region": "Auckland", "name": "Auckland, New Zealand"},
    "wellington": {"lat": -41.29, "lng": 174.77, "country": "New Zealand", "region": "Wellington", "name": "Wellington, New Zealand"},
    "suva": {"lat": -18.14, "lng": 178.44, "country": "Fiji", "region": "Central", "name": "Suva, Fiji"},
    "port moresby": {"lat": -9.44, "lng": 147.18, "country": "Papua New Guinea", "region": "NCD", "name": "Port Moresby, Papua New Guinea"},

    # Latin America & Caribbean (Local additions)
    "kingston": {"lat": 17.97, "lng": -76.79, "country": "Jamaica", "region": "Surrey", "name": "Kingston, Jamaica"},
    "port of spain": {"lat": 10.66, "lng": -61.51, "country": "Trinidad and Tobago", "region": "Port of Spain", "name": "Port of Spain, Trinidad and Tobago"},
    "montevideo": {"lat": -34.90, "lng": -56.16, "country": "Uruguay", "region": "Montevideo", "name": "Montevideo, Uruguay"},
    "medellin": {"lat": 6.24, "lng": -75.58, "country": "Colombia", "region": "Antioquia", "name": "Medellin, Colombia"},
    "valparaiso": {"lat": -33.04, "lng": -71.61, "country": "Chile", "region": "Valparaiso", "name": "Valparaiso, Chile"},

    # Europe (Local additions)
    "gdansk": {"lat": 54.35, "lng": 18.64, "country": "Poland", "region": "Pomerania", "name": "Gdansk, Poland"},
    "thessaloniki": {"lat": 40.64, "lng": 22.94, "country": "Greece", "region": "Central Macedonia", "name": "Thessaloniki, Greece"},
    "klaipeda": {"lat": 55.70, "lng": 21.14, "country": "Lithuania", "region": "Klaipeda", "name": "Klaipeda, Lithuania"}
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
    "pakistan": {"lat": 30.37, "lng": 69.34, "country": "Pakistan", "name": "Pakistan"},
    "bangladesh": {"lat": 23.68, "lng": 90.35, "country": "Bangladesh", "name": "Bangladesh"},
    "sri lanka": {"lat": 7.87, "lng": 80.77, "country": "Sri Lanka", "name": "Sri Lanka"},
    "nepal": {"lat": 28.39, "lng": 84.12, "country": "Nepal", "name": "Nepal"},
    "thailand": {"lat": 15.87, "lng": 100.99, "country": "Thailand", "name": "Thailand"},
    "indonesia": {"lat": -0.78, "lng": 113.92, "country": "Indonesia", "name": "Indonesia"},
    "philippines": {"lat": 12.87, "lng": 121.77, "country": "Philippines", "name": "Philippines"},
    "vietnam": {"lat": 14.05, "lng": 108.27, "country": "Vietnam", "name": "Vietnam"},
    "malaysia": {"lat": 4.21, "lng": 101.97, "country": "Malaysia", "name": "Malaysia"},
    "south korea": {"lat": 35.90, "lng": 127.76, "country": "South Korea", "name": "South Korea"},
    "taiwan": {"lat": 23.69, "lng": 120.96, "country": "Taiwan", "name": "Taiwan"},
    "saudi arabia": {"lat": 23.88, "lng": 45.07, "country": "Saudi Arabia", "name": "Saudi Arabia"},
    "united arab emirates": {"lat": 23.42, "lng": 53.84, "country": "United Arab Emirates", "name": "United Arab Emirates"},
    "uae": {"lat": 23.42, "lng": 53.84, "country": "United Arab Emirates", "name": "United Arab Emirates"},
    "egypt": {"lat": 26.82, "lng": 30.80, "country": "Egypt", "name": "Egypt"},
    "jordan": {"lat": 30.58, "lng": 36.23, "country": "Jordan", "name": "Jordan"},
    "lebanon": {"lat": 33.85, "lng": 35.86, "country": "Lebanon", "name": "Lebanon"},
    "morocco": {"lat": 31.79, "lng": -7.09, "country": "Morocco", "name": "Morocco"},
    "kenya": {"lat": -0.02, "lng": 37.90, "country": "Kenya", "name": "Kenya"},
    "nigeria": {"lat": 9.08, "lng": 8.67, "country": "Nigeria", "name": "Nigeria"},
    "ghana": {"lat": 7.94, "lng": -1.02, "country": "Ghana", "name": "Ghana"},
    "sudan": {"lat": 12.86, "lng": 30.21, "country": "Sudan", "name": "Sudan"},
    "ethiopia": {"lat": 9.14, "lng": 40.48, "country": "Ethiopia", "name": "Ethiopia"},
    "south africa": {"lat": -30.55, "lng": 22.93, "country": "South Africa", "name": "South Africa"},
    "australia": {"lat": -25.27, "lng": 133.77, "country": "Australia", "name": "Australia"},
    "new zealand": {"lat": -40.90, "lng": 174.88, "country": "New Zealand", "name": "New Zealand"},
    "fiji": {"lat": -17.71, "lng": 178.06, "country": "Fiji", "name": "Fiji"},
    "colombia": {"lat": 4.57, "lng": -74.29, "country": "Colombia", "name": "Colombia"},
    "chile": {"lat": -35.67, "lng": -71.54, "country": "Chile", "name": "Chile"},
    "jamaica": {"lat": 18.10, "lng": -77.29, "country": "Jamaica", "name": "Jamaica"},
    "poland": {"lat": 51.91, "lng": 19.14, "country": "Poland", "name": "Poland"},
    "greece": {"lat": 39.07, "lng": 21.82, "country": "Greece", "name": "Greece"},
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
