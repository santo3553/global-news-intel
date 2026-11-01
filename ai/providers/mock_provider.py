import re
import math
import hashlib
from typing import List
from ai.providers.base import AIProvider
from ai.schemas.extraction import ExtractedEventData, ExtractedLocation, ExtractedEntity


class MockAIProvider(AIProvider):
    """
    Deterministic rule-based AI provider for local testing, CI, and instant offline operation.
    Generates structured Pydantic event data and dense 384-dimensional embeddings.
    """

    async def extract_event(self, title: str, text: str) -> ExtractedEventData:
        # Detect non-Latin scripts (Bengali, Hindi, Urdu, Arabic) and auto-translate
        full_sample = f"{title} {text}"
        if any('\u0980' <= c <= '\u09FF' for c in full_sample):
            eng_title = await self.translate_to_english(title, "bn")
            eng_text = await self.translate_to_english(text, "bn")
            data = await self.extract_event(eng_title, eng_text)
            return data
        elif any('\u0900' <= c <= '\u097F' for c in full_sample):
            eng_title = await self.translate_to_english(title, "hi")
            eng_text = await self.translate_to_english(text, "hi")
            data = await self.extract_event(eng_title, eng_text)
            return data
        elif any('\u0600' <= c <= '\u06FF' for c in full_sample):
            is_ur = any(c in "ٹڈڑںےہ" for c in full_sample)
            lang = "ur" if is_ur else "ar"
            eng_title = await self.translate_to_english(title, lang)
            eng_text = await self.translate_to_english(text, lang)
            data = await self.extract_event(eng_title, eng_text)
            return data

        combined = f"{title} {text}".lower()

        # 1. Category and Subcategory Detection
        category = "general"
        subcategory = None
        severity = 0.5
        human_impact = 5.0
        global_impact = 5.0
        novelty = 0.6

        if any(w in combined for w in [
            "earthquake", "quake", "tremor", "tsunami", "flood", "hurricane", "typhoon", "wildfire", "volcano",
            "terremoto", "sismo", "inundacion", "inundación", "incendio"
        ]):
            category = "natural_disaster"
            if any(w in combined for w in ["earthquake", "quake", "tremor", "terremoto", "sismo"]):
                subcategory = "earthquake"
                severity = 0.85
                human_impact = 8.0
                global_impact = 7.5
                novelty = 0.8
            elif "tsunami" in combined:
                subcategory = "tsunami"
                severity = 0.90
                human_impact = 8.5
        elif any(w in combined for w in [
            "summit", "accord", "treaty", "election", "vote", "parliament", "president", "diplomat", "ratify",
            "elecciones", "cumbre", "tratado", "acuerdo", "votación", "votacion"
        ]):
            category = "politics"
            subcategory = "diplomacy" if any(w in combined for w in ["summit", "treaty", "accord", "cumbre", "tratado", "acuerdo"]) else "election"
            severity = 0.40
            human_impact = 6.0
            global_impact = 8.5
            novelty = 0.7
        elif any(w in combined for w in [
            "security", "sabotage", "drone", "missile", "military", "defense", "interconnector", "fluctuation",
            "policía", "policia", "ejército", "ejercito", "ataque"
        ]):
            category = "security"
            subcategory = "infrastructure" if "grid" in combined or "interconnector" in combined else "defense"
            severity = 0.70
            human_impact = 6.5
            global_impact = 7.0
            novelty = 0.75
        elif any(w in combined for w in ["telescope", "nasa", "exoplanet", "astronomy", "discovery", "space", "orbit"]):
            category = "science"
            subcategory = "astronomy"
            severity = 0.20
            human_impact = 3.5
            global_impact = 8.0
            novelty = 0.95
        elif any(w in combined for w in [
            "trade", "mercosur", "tariff", "asean", "economy", "inflation", "gdp", "market",
            "inflación", "inflacion", "comercio", "arancel"
        ]):
            category = "economy"
            subcategory = "trade"
            severity = 0.35
            human_impact = 5.5
            global_impact = 7.2
            novelty = 0.65

        # 2. Location Detection using comprehensive offline gazetteer
        from workers.extraction.geocoder import Geocoder
        geocoder = Geocoder()
        resolved = geocoder.resolve(
            raw_name="",
            country_hint=None,
            text_context=combined
        )

        location = ExtractedLocation(
            name=resolved.name,
            country=resolved.country,
            admin_region=resolved.admin_region,
            city=resolved.city,
            latitude=resolved.latitude,
            longitude=resolved.longitude,
            precision=resolved.precision,
            location_confidence=resolved.location_confidence
        )

        # 3. Entities
        entities: List[ExtractedEntity] = []
        if resolved.country:
            entities.append(ExtractedEntity(name=resolved.country, type="country"))
        if resolved.city:
            entities.append(ExtractedEntity(name=resolved.city, type="location"))

        for org in ["Reuters", "Associated Press", "BBC", "NHK", "NASA", "UN", "Mercosur", "ASEAN", "European Union", "JMA"]:
            if org.lower() in combined:
                entities.append(ExtractedEntity(name=org, type="organization"))

        # 4. Factual Claims
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 20]
        claims = sentences[:4] if sentences else [title]

        return ExtractedEventData(
            event_title=title.strip(),
            category=category,
            subcategory=subcategory,
            location=location,
            entities=entities,
            claims=claims,
            severity=severity,
            novelty=novelty,
            confidence=0.90 if len(entities) > 1 else 0.75,
            human_impact_estimate=human_impact,
            global_impact_estimate=global_impact
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic 384-dimensional unit-normalized embedding vector.
        Combines token hashing, sub-character trigrams, and semantic concept clustering.
        """
        dim = 384
        vec = [0.0] * dim
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        tokens = re.findall(r"\b\w{3,}\b", normalized)

        # Trigrams and tokens hashed into 384 buckets
        for token in tokens:
            # Word bucket
            h_word = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
            vec[h_word] += 1.0

            # Sub-character trigrams
            for i in range(len(token) - 2):
                trigram = token[i:i + 3]
                h_tri = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16) % dim
                vec[h_tri] += 0.3

        # Semantic Concept Clusters (simulates dense embeddings for related concepts)
        SEMANTIC_CLUSTERS = {
            "seismic_disaster": ["earthquake", "quake", "tremor", "tsunami", "seismic", "aftershock", "epicenter", "kyushu", "miyazaki"],
            "storm_disaster": ["hurricane", "typhoon", "cyclone", "storm", "flood", "wildfire"],
            "diplomacy_accord": ["treaty", "summit", "accord", "diplomat", "negotiate", "consensus", "climate", "geneva"],
            "security_conflict": ["military", "missile", "drone", "sabotage", "attack", "defense", "security", "baltic", "interconnector"],
            "space_science": ["telescope", "exoplanet", "nasa", "astronomy", "satellite", "space"],
            "economic_trade": ["tariff", "trade", "mercosur", "inflation", "market", "economy", "argentina"]
        }

        for cluster_name, keywords in SEMANTIC_CLUSTERS.items():
            matched = sum(1 for kw in keywords if kw in normalized)
            if matched > 0:
                h_cluster = int(hashlib.md5(cluster_name.encode("utf-8")).hexdigest(), 16) % dim
                # Boost semantic concept dimensions
                for offset in range(4):
                    vec[(h_cluster + offset) % dim] += 1.5 * matched

        # L2 Unit Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]
        else:
            vec[0] = 1.0

        return vec

    async def summarize_event(self, prompt: str) -> str:
        return (
            "### What Happened?\n"
            "A notable event was recorded and verified by multiple reporting sources.\n\n"
            "### Why It Matters\n"
            "This development has regional and global implications for civil infrastructure and policy.\n\n"
            "### What Is Known\n"
            "* Multiple independent sources have confirmed initial reports.\n"
            "* Regional monitoring services are actively tracking developments.\n\n"
            "### What Is Uncertain\n"
            "* Long-term secondary effects and comprehensive impact assessments are ongoing."
        )

    async def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        Automated translation engine for native-language news (Bengali, Hindi, Urdu, Arabic, Spanish).
        Converts native headlines and reports into clean, canonical English while
        preserving local municipal/district granularity and numerical counts.
        """
        if not text or source_lang == "en":
            return text

        lang = source_lang.lower().strip()
        cleaned = text.strip()

        # Bengali Dictionary & Patterns
        if lang == "bn":
            DICTIONARY_BN = [
                ("ভূমিকম্প", "earthquake"),
                ("বন্যা", "flood"),
                ("ঘূর্ণিঝড়", "cyclone"),
                ("নিহত", "killed"),
                ("আহত", "injured"),
                ("সমাবেশ", "rally"),
                ("নির্বাচন", "election"),
                ("আগুন", "fire"),
                ("বিক্ষোভ", "protest"),
                ("পুলিশ", "police"),
                ("গ্রেফতার", "arrested"),
                ("চুক্তি", "accord"),
                ("মুদ্রা", "currency"),
                ("ডলার", "dollar"),
                ("দুর্ঘটনা", "accident"),
                ("যানবাহন", "vehicles"),
                ("সড়ক", "highway"),
                ("উদ্ধার", "rescue"),
                ("হাসপাতাল", "hospital"),
                ("ঢাকা", "Dhaka"),
                ("চট্টগ্রাম", "Chittagong"),
                ("সিলেট", "Sylhet"),
                ("রাজশাহী", "Rajshahi"),
                ("খুলনা", "Khulna"),
                ("বরিশাল", "Barishal"),
                ("রংপুর", "Rangpur"),
                ("ময়মনসিংহ", "Mymensingh"),
                ("ধানমন্ডি", "Dhanmondi"),
                ("মিরপুর", "Mirpur"),
                ("উত্তরা", "Uttara"),
                ("গুলশান", "Gulshan"),
                ("মতিঝিল", "Motijheel"),
                ("চকবাজার", "Chawkbazar"),
                ("কারওয়ান বাজার", "Karwan Bazar"),
                ("যাত্রাবাড়ী", "Jatrabari"),
                ("প্রধানমন্ত্রী", "Prime Minister"),
                ("রাষ্ট্রপতি", "President"),
                ("সরকার", "government"),
                ("প্রশাসন", "administration"),
                ("আদালত", "court"),
                ("জরিমানা", "fine"),
                ("অভিযান", "operation"),
            ]
            translated = cleaned
            for native, eng in DICTIONARY_BN:
                translated = re.sub(re.escape(native), eng, translated, flags=re.IGNORECASE)
            
            if any(ord(c) > 127 for c in translated):
                found_locs = [eng for native, eng in DICTIONARY_BN[19:35] if native in cleaned or eng.lower() in translated.lower()]
                loc_str = found_locs[0] if found_locs else "Dhaka, Bangladesh"
                core_eng = re.sub(r'[^\x00-\x7F]+', ' ', translated).strip()
                if len(core_eng) > 10:
                    return f"{core_eng} ({loc_str})"
                return f"Municipal operation and public safety incident in {loc_str}"
            return translated

        # Hindi Dictionary & Patterns
        elif lang == "hi":
            DICTIONARY_HI = [
                ("भूकंप", "earthquake"),
                ("बाढ़", "flood"),
                ("तूफान", "storm"),
                ("चक्रवात", "cyclone"),
                ("मौत", "casualties"),
                ("घायल", "injured"),
                ("पुलिस", "police"),
                ("विरोध", "protest"),
                ("चुनाव", "election"),
                ("आग", "fire"),
                ("गिरफ्तार", "arrested"),
                ("समझौता", "accord"),
                ("अर्थव्यवस्था", "economy"),
                ("संसद", "parliament"),
                ("दिल्ली", "Delhi"),
                ("नई दिल्ली", "New Delhi"),
                ("वाराणसी", "Varanasi"),
                ("लखनऊ", "Lucknow"),
                ("कानपुर", "Kanpur"),
                ("जयपुर", "Jaipur"),
                ("पटना", "Patna"),
                ("आगरा", "Agra"),
                ("भोपाल", "Bhopal"),
                ("मुंबई", "Mumbai"),
                ("गाजियाबाद", "Ghaziabad"),
                ("नोएडा", "Noida"),
                ("प्रधानमंत्री", "Prime Minister"),
                ("मुख्यमंत्री", "Chief Minister"),
                ("सरकार", "government"),
            ]
            translated = cleaned
            for native, eng in DICTIONARY_HI:
                translated = re.sub(re.escape(native), eng, translated, flags=re.IGNORECASE)
            if any(ord(c) > 127 for c in translated):
                found_locs = [eng for native, eng in DICTIONARY_HI[14:26] if native in cleaned or eng.lower() in translated.lower()]
                loc_str = found_locs[0] if found_locs else "New Delhi, India"
                core_eng = re.sub(r'[^\x00-\x7F]+', ' ', translated).strip()
                if len(core_eng) > 10:
                    return f"{core_eng} ({loc_str})"
                return f"Regional development and municipal operation in {loc_str}"
            return translated

        # Urdu Dictionary & Patterns
        elif lang == "ur":
            DICTIONARY_UR = [
                ("زلزلہ", "earthquake"),
                ("سیلاب", "flood"),
                ("ہلاکت", "killed"),
                ("زخمی", "injured"),
                ("فوج", "military"),
                ("پولیس", "police"),
                ("احتجاج", "protest"),
                ("دھماکہ", "explosion"),
                ("وزیر اعظم", "Prime Minister"),
                ("پارلیمنٹ", "parliament"),
                ("معیشت", "economy"),
                ("اسلام آباد", "Islamabad"),
                ("کراچی", "Karachi"),
                ("لاہور", "Lahore"),
                ("پشاور", "Peshawar"),
                ("کوئٹہ", "Quetta"),
                ("راولپنڈی", "Rawalpindi"),
            ]
            translated = cleaned
            for native, eng in DICTIONARY_UR:
                translated = re.sub(re.escape(native), eng, translated, flags=re.IGNORECASE)
            if any(ord(c) > 127 for c in translated):
                found_locs = [eng for native, eng in DICTIONARY_UR[11:] if native in cleaned or eng.lower() in translated.lower()]
                loc_str = found_locs[0] if found_locs else "Islamabad, Pakistan"
                core_eng = re.sub(r'[^\x00-\x7F]+', ' ', translated).strip()
                if len(core_eng) > 10:
                    return f"{core_eng} ({loc_str})"
                return f"Security and civic operations report from {loc_str}"
            return translated

        # Arabic Dictionary & Patterns
        elif lang == "ar":
            DICTIONARY_AR = [
                ("زلزال", "earthquake"),
                ("فيضان", "flood"),
                ("انفجار", "explosion"),
                ("قصف", "strike"),
                ("جيش", "army"),
                ("قتيل", "killed"),
                ("قتلى", "fatalities"),
                ("جريح", "injured"),
                ("مظاهرات", "protests"),
                ("اتفاق", "accord"),
                ("قمة", "summit"),
                ("اقتصاد", "economy"),
                ("إطلاق نار", "shooting"),
                ("القدس", "Jerusalem"),
                ("غزة", "Gaza"),
                ("بيروت", "Beirut"),
                ("دمشق", "Damascus"),
                ("بغداد", "Baghdad"),
                ("الرياض", "Riyadh"),
                ("القاهرة", "Cairo"),
                ("صنعاء", "Sanaa"),
                ("الدوحة", "Doha"),
            ]
            translated = cleaned
            for native, eng in DICTIONARY_AR:
                translated = re.sub(re.escape(native), eng, translated, flags=re.IGNORECASE)
            if any(ord(c) > 127 for c in translated):
                found_locs = [eng for native, eng in DICTIONARY_AR[13:] if native in cleaned or eng.lower() in translated.lower()]
                loc_str = found_locs[0] if found_locs else "Middle East"
                core_eng = re.sub(r'[^\x00-\x7F]+', ' ', translated).strip()
                if len(core_eng) > 10:
                    return f"{core_eng} ({loc_str})"
                return f"Regional development report from {loc_str}"
            return translated

        # Spanish Dictionary & Patterns
        elif lang == "es":
            DICTIONARY_ES = [
                (r"\bterremoto\b", "earthquake"),
                (r"\bsismo\b", "tremor"),
                (r"\binundaci[oó]n\b", "flood"),
                (r"\bincendio\b", "wildfire"),
                (r"\bhurac[aá]n\b", "hurricane"),
                (r"\bmuertos\b", "dead"),
                (r"\bfallecidos\b", "fatalities"),
                (r"\bheridos\b", "injured"),
                (r"\belecciones\b", "elections"),
                (r"\bvotaci[oó]n\b", "voting"),
                (r"\bprotesta\b", "protest"),
                (r"\bmanifestaci[oó]n\b", "demonstration"),
                (r"\bpolic[ií]a\b", "police"),
                (r"\bcumbre\b", "summit"),
                (r"\btratado\b", "treaty"),
                (r"\bacuerdo\b", "accord"),
                (r"\binflaci[oó]n\b", "inflation"),
                (r"\bgobierno\b", "government"),
                (r"\bpresidente\b", "president"),
                (r"\bparo\b", "strike"),
            ]
            translated = cleaned
            for pat, eng in DICTIONARY_ES:
                translated = re.sub(pat, eng, translated, flags=re.IGNORECASE)
            return translated

        return cleaned
