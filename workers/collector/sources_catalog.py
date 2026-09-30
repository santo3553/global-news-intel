"""Curated catalog of reliable, publicly accessible global news sources and RSS feeds."""

from typing import List, Dict, Any

CURATED_SOURCES: List[Dict[str, Any]] = [
    # Global & International Wires
    {
        "id": "src-reuters-world",
        "name": "Reuters World",
        "domain": "reuters.com",
        "feed_url": "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",
        "source_type": "rss",
        "country": "GB",
        "language": "en",
        "reliability_score": 0.95,
        "active": True
    },
    {
        "id": "src-ap-top",
        "name": "Associated Press Top News",
        "domain": "apnews.com",
        "feed_url": "https://apnews.com/rss/topnews",
        "source_type": "rss",
        "country": "US",
        "language": "en",
        "reliability_score": 0.95,
        "active": True
    },
    {
        "id": "src-bbc-world",
        "name": "BBC News World",
        "domain": "bbc.com",
        "feed_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "source_type": "rss",
        "country": "GB",
        "language": "en",
        "reliability_score": 0.92,
        "active": True
    },
    {
        "id": "src-npr-world",
        "name": "NPR News World",
        "domain": "npr.org",
        "feed_url": "https://feeds.npr.org/1004/rss.xml",
        "source_type": "rss",
        "country": "US",
        "language": "en",
        "reliability_score": 0.90,
        "active": True
    },

    # Europe
    {
        "id": "src-dw-world",
        "name": "Deutsche Welle World",
        "domain": "dw.com",
        "feed_url": "https://rss.dw.com/rdf/rss-en-all",
        "source_type": "rss",
        "country": "DE",
        "language": "en",
        "reliability_score": 0.90,
        "active": True
    },
    {
        "id": "src-france24-en",
        "name": "France 24 English",
        "domain": "france24.com",
        "feed_url": "https://www.france24.com/en/rss",
        "source_type": "rss",
        "country": "FR",
        "language": "en",
        "reliability_score": 0.88,
        "active": True
    },
    {
        "id": "src-theguardian-world",
        "name": "The Guardian World",
        "domain": "theguardian.com",
        "feed_url": "https://www.theguardian.com/world/rss",
        "source_type": "rss",
        "country": "GB",
        "language": "en",
        "reliability_score": 0.87,
        "active": True
    },
    {
        "id": "src-euronews-en",
        "name": "Euronews World",
        "domain": "euronews.com",
        "feed_url": "https://www.euronews.com/rss?format=mrss&level=theme&name=news",
        "source_type": "rss",
        "country": "FR",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },

    # Asia-Pacific
    {
        "id": "src-nhk-world",
        "name": "NHK World Japan",
        "domain": "nhk.or.jp",
        "feed_url": "https://www3.nhk.or.jp/nhkworld/en/news/rss/all.xml",
        "source_type": "rss",
        "country": "JP",
        "language": "en",
        "reliability_score": 0.92,
        "active": True
    },
    {
        "id": "src-japantimes",
        "name": "The Japan Times",
        "domain": "japantimes.co.jp",
        "feed_url": "https://www.japantimes.co.jp/feed/",
        "source_type": "rss",
        "country": "JP",
        "language": "en",
        "reliability_score": 0.88,
        "active": True
    },
    {
        "id": "src-cna-asia",
        "name": "Channel NewsAsia",
        "domain": "channelnewsasia.com",
        "feed_url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
        "source_type": "rss",
        "country": "SG",
        "language": "en",
        "reliability_score": 0.88,
        "active": True
    },
    {
        "id": "src-abc-au-world",
        "name": "ABC News Australia World",
        "domain": "abc.net.au",
        "feed_url": "https://www.abc.net.au/news/feed/52278/rss.xml",
        "source_type": "rss",
        "country": "AU",
        "language": "en",
        "reliability_score": 0.90,
        "active": True
    },
    {
        "id": "src-timesofindia-world",
        "name": "Times of India World",
        "domain": "timesofindia.indiatimes.com",
        "feed_url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
        "source_type": "rss",
        "country": "IN",
        "language": "en",
        "reliability_score": 0.80,
        "active": True
    },

    # Middle East & Africa
    {
        "id": "src-aljazeera-en",
        "name": "Al Jazeera English",
        "domain": "aljazeera.com",
        "feed_url": "https://www.aljazeera.com/xml/rss/all.xml",
        "source_type": "rss",
        "country": "QA",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-haaretz-en",
        "name": "Haaretz English",
        "domain": "haaretz.com",
        "feed_url": "https://www.haaretz.com/cmlink/1.4605929",
        "source_type": "rss",
        "country": "IL",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },
    {
        "id": "src-allafrica-latest",
        "name": "AllAfrica Latest",
        "domain": "allafrica.com",
        "feed_url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",
        "source_type": "rss",
        "country": "ZA",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },

    # Americas
    {
        "id": "src-cbc-world",
        "name": "CBC News World",
        "domain": "cbc.ca",
        "feed_url": "https://www.cbc.ca/cmlink/rss-world",
        "source_type": "rss",
        "country": "CA",
        "language": "en",
        "reliability_score": 0.91,
        "active": True
    },
    {
        "id": "src-mercopress-en",
        "name": "MercoPress South America",
        "domain": "en.mercopress.com",
        "feed_url": "https://en.mercopress.com/rss/",
        "source_type": "rss",
        "country": "UY",
        "language": "en",
        "reliability_score": 0.80,
        "active": True
    },
    {
        "id": "src-un-news",
        "name": "UN News Global",
        "domain": "news.un.org",
        "feed_url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "source_type": "rss",
        "country": "UN",
        "language": "en",
        "reliability_score": 0.96,
        "active": True
    },
    {
        "id": "src-who-outbreaks",
        "name": "WHO Disease Outbreaks",
        "domain": "who.int",
        "feed_url": "https://www.who.int/feeds/entity/don/en/rss.xml",
        "source_type": "rss",
        "country": "UN",
        "language": "en",
        "reliability_score": 0.98,
        "active": True
    }
]
