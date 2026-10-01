"""Curated catalog of reliable, publicly accessible global and local news sources and RSS feeds."""

from typing import List, Dict, Any

CURATED_SOURCES: List[Dict[str, Any]] = [
    # ==========================================
    # Global & International Wires
    # ==========================================
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
    },

    # ==========================================
    # South Asia (Local & National)
    # ==========================================
    {
        "id": "src-thehindu-in",
        "name": "The Hindu",
        "domain": "thehindu.com",
        "feed_url": "https://www.thehindu.com/news/national/feeder/default.rss",
        "source_type": "rss",
        "country": "IN",
        "language": "en",
        "reliability_score": 0.88,
        "active": True
    },
    {
        "id": "src-indianexpress-in",
        "name": "The Indian Express",
        "domain": "indianexpress.com",
        "feed_url": "https://indianexpress.com/section/india/feed/",
        "source_type": "rss",
        "country": "IN",
        "language": "en",
        "reliability_score": 0.86,
        "active": True
    },
    {
        "id": "src-deccanherald-in",
        "name": "Deccan Herald (Bangalore)",
        "domain": "deccanherald.com",
        "feed_url": "https://www.deccanherald.com/rss/national.rss",
        "source_type": "rss",
        "country": "IN",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-timesofindia-world",
        "name": "Times of India",
        "domain": "timesofindia.indiatimes.com",
        "feed_url": "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
        "source_type": "rss",
        "country": "IN",
        "language": "en",
        "reliability_score": 0.80,
        "active": True
    },
    {
        "id": "src-dawn-pk",
        "name": "Dawn (Pakistan)",
        "domain": "dawn.com",
        "feed_url": "https://www.dawn.com/feeds/home/",
        "source_type": "rss",
        "country": "PK",
        "language": "en",
        "reliability_score": 0.86,
        "active": True
    },
    {
        "id": "src-dailystar-bd",
        "name": "The Daily Star (Bangladesh)",
        "domain": "thedailystar.net",
        "feed_url": "https://www.thedailystar.net/frontpage/rss.xml",
        "source_type": "rss",
        "country": "BD",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-dailymirror-lk",
        "name": "Daily Mirror (Sri Lanka)",
        "domain": "dailymirror.lk",
        "feed_url": "https://www.dailymirror.lk/RSS_Feeds/breaking_news",
        "source_type": "rss",
        "country": "LK",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },
    {
        "id": "src-kathmandupost-np",
        "name": "The Kathmandu Post (Nepal)",
        "domain": "kathmandupost.com",
        "feed_url": "https://kathmandupost.com/rss",
        "source_type": "rss",
        "country": "NP",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },

    # ==========================================
    # Southeast Asia (Local & National)
    # ==========================================
    {
        "id": "src-straitstimes-sg",
        "name": "The Straits Times (Singapore)",
        "domain": "straitstimes.com",
        "feed_url": "https://www.straitstimes.com/news/asia/rss.xml",
        "source_type": "rss",
        "country": "SG",
        "language": "en",
        "reliability_score": 0.90,
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
        "id": "src-jakartapost-id",
        "name": "The Jakarta Post (Indonesia)",
        "domain": "thejakartapost.com",
        "feed_url": "https://www.thejakartapost.com/rss",
        "source_type": "rss",
        "country": "ID",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-bangkokpost-th",
        "name": "Bangkok Post (Thailand)",
        "domain": "bangkokpost.com",
        "feed_url": "https://www.bangkokpost.com/rss/data/mostrecent.xml",
        "source_type": "rss",
        "country": "TH",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-inquirer-ph",
        "name": "Philippine Daily Inquirer",
        "domain": "inquirer.net",
        "feed_url": "https://newsinfo.inquirer.net/feed",
        "source_type": "rss",
        "country": "PH",
        "language": "en",
        "reliability_score": 0.83,
        "active": True
    },
    {
        "id": "src-vnexpress-vn",
        "name": "VnExpress International (Vietnam)",
        "domain": "e.vnexpress.net",
        "feed_url": "https://e.vnexpress.net/rss/news.rss",
        "source_type": "rss",
        "country": "VN",
        "language": "en",
        "reliability_score": 0.83,
        "active": True
    },
    {
        "id": "src-thestar-my",
        "name": "The Star (Malaysia)",
        "domain": "thestar.com.my",
        "feed_url": "https://www.thestar.com.my/rss/news/nation",
        "source_type": "rss",
        "country": "MY",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },

    # ==========================================
    # East Asia (Local & National)
    # ==========================================
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
        "id": "src-mainichi-jp",
        "name": "Mainichi Shimbun (Japan)",
        "domain": "mainichi.jp",
        "feed_url": "https://mainichi.jp/english/rss/etc/mainichi-flash.rdf",
        "source_type": "rss",
        "country": "JP",
        "language": "en",
        "reliability_score": 0.88,
        "active": True
    },
    {
        "id": "src-koreaherald-kr",
        "name": "The Korea Herald (South Korea)",
        "domain": "koreaherald.com",
        "feed_url": "http://www.koreaherald.com/rss/",
        "source_type": "rss",
        "country": "KR",
        "language": "en",
        "reliability_score": 0.86,
        "active": True
    },
    {
        "id": "src-focustaiwan-tw",
        "name": "Focus Taiwan",
        "domain": "focustaiwan.tw",
        "feed_url": "https://focustaiwan.tw/rss/all.xml",
        "source_type": "rss",
        "country": "TW",
        "language": "en",
        "reliability_score": 0.87,
        "active": True
    },
    {
        "id": "src-scmp-hk",
        "name": "South China Morning Post",
        "domain": "scmp.com",
        "feed_url": "https://www.scmp.com/rss/91/feed",
        "source_type": "rss",
        "country": "HK",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },

    # ==========================================
    # Central Asia, Caspian & Caucasus (Local & Regional)
    # ==========================================
    {
        "id": "src-astanatimes-kz",
        "name": "The Astana Times (Kazakhstan)",
        "domain": "astanatimes.com",
        "feed_url": "https://astanatimes.com/feed/",
        "source_type": "rss",
        "country": "KZ",
        "language": "en",
        "reliability_score": 0.86,
        "active": True
    },
    {
        "id": "src-timesca-centralasia",
        "name": "The Times of Central Asia",
        "domain": "timesca.com",
        "feed_url": "https://timesca.com/feed/",
        "source_type": "rss",
        "country": "KZ",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-eurasianet-regional",
        "name": "Eurasianet (Central Asia & Caucasus)",
        "domain": "eurasianet.org",
        "feed_url": "https://eurasianet.org/feed",
        "source_type": "rss",
        "country": "GE",
        "language": "en",
        "reliability_score": 0.88,
        "active": True
    },
    {
        "id": "src-uzdaily-uz",
        "name": "UzDaily (Uzbekistan)",
        "domain": "uzdaily.uz",
        "feed_url": "https://www.uzdaily.uz/en/rss",
        "source_type": "rss",
        "country": "UZ",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-azernews-az",
        "name": "Azernews (Azerbaijan & Caspian)",
        "domain": "azernews.az",
        "feed_url": "https://www.azernews.az/rss/",
        "source_type": "rss",
        "country": "AZ",
        "language": "en",
        "reliability_score": 0.83,
        "active": True
    },
    {
        "id": "src-agenda-ge",
        "name": "Agenda.ge (Georgia & Caucasus)",
        "domain": "agenda.ge",
        "feed_url": "https://agenda.ge/en/feed",
        "source_type": "rss",
        "country": "GE",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-hurriyet-tr",
        "name": "Hürriyet Daily News (Turkey)",
        "domain": "hurriyetdailynews.com",
        "feed_url": "https://www.hurriyetdailynews.com/rss",
        "source_type": "rss",
        "country": "TR",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-tolonews-af",
        "name": "TOLOnews (Afghanistan)",
        "domain": "tolonews.com",
        "feed_url": "https://tolonews.com/rss/all",
        "source_type": "rss",
        "country": "AF",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },

    # ==========================================
    # Middle East & North Africa (Local & Regional)
    # ==========================================
    {
        "id": "src-arabnews-sa",
        "name": "Arab News (Saudi Arabia)",
        "domain": "arabnews.com",
        "feed_url": "https://www.arabnews.com/rss.xml",
        "source_type": "rss",
        "country": "SA",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-thenational-ae",
        "name": "The National (UAE)",
        "domain": "thenationalnews.com",
        "feed_url": "https://www.thenationalnews.com/arc/outboundfeeds/rss/category/mena/",
        "source_type": "rss",
        "country": "AE",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
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
        "id": "src-timesofisrael-il",
        "name": "The Times of Israel",
        "domain": "timesofisrael.com",
        "feed_url": "https://www.timesofisrael.com/feed/",
        "source_type": "rss",
        "country": "IL",
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
        "id": "src-egyptindependent-eg",
        "name": "Egypt Independent",
        "domain": "egyptindependent.com",
        "feed_url": "https://egyptindependent.com/feed/",
        "source_type": "rss",
        "country": "EG",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },
    {
        "id": "src-jordantimes-jo",
        "name": "The Jordan Times",
        "domain": "jordantimes.com",
        "feed_url": "https://jordantimes.com/rss.xml",
        "source_type": "rss",
        "country": "JO",
        "language": "en",
        "reliability_score": 0.83,
        "active": True
    },
    {
        "id": "src-lorient-lb",
        "name": "L'Orient Today (Lebanon)",
        "domain": "today.lorientlejour.com",
        "feed_url": "https://today.lorientlejour.com/rss",
        "source_type": "rss",
        "country": "LB",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-moroccoworldnews-ma",
        "name": "Morocco World News",
        "domain": "moroccoworldnews.com",
        "feed_url": "https://www.moroccoworldnews.com/feed/",
        "source_type": "rss",
        "country": "MA",
        "language": "en",
        "reliability_score": 0.81,
        "active": True
    },

    # ==========================================
    # Sub-Saharan Africa (Local & Regional)
    # ==========================================
    {
        "id": "src-dailynation-ke",
        "name": "Daily Nation (Kenya)",
        "domain": "nation.africa",
        "feed_url": "https://nation.africa/kenya/rss",
        "source_type": "rss",
        "country": "KE",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-theeastafrican-ke",
        "name": "The EastAfrican",
        "domain": "theeastafrican.co.ke",
        "feed_url": "https://www.theeastafrican.co.ke/rss",
        "source_type": "rss",
        "country": "KE",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-premiumtimes-ng",
        "name": "Premium Times (Nigeria)",
        "domain": "premiumtimesng.com",
        "feed_url": "https://www.premiumtimesng.com/feed",
        "source_type": "rss",
        "country": "NG",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-news24-za",
        "name": "News24 (South Africa)",
        "domain": "news24.com",
        "feed_url": "https://feeds.24.com/articles/news24/SouthAfrica/rss",
        "source_type": "rss",
        "country": "ZA",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-mailandguardian-za",
        "name": "Mail & Guardian (South Africa)",
        "domain": "mg.co.za",
        "feed_url": "https://mg.co.za/feed/",
        "source_type": "rss",
        "country": "ZA",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-ghanaweb-gh",
        "name": "GhanaWeb",
        "domain": "ghanaweb.com",
        "feed_url": "https://www.ghanaweb.com/GhanaHomePage/rss/feed.xml",
        "source_type": "rss",
        "country": "GH",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },
    {
        "id": "src-sudantribune-sd",
        "name": "Sudan Tribune",
        "domain": "sudantribune.com",
        "feed_url": "https://sudantribune.com/feed/",
        "source_type": "rss",
        "country": "SD",
        "language": "en",
        "reliability_score": 0.83,
        "active": True
    },
    {
        "id": "src-addisstandard-et",
        "name": "Addis Standard (Ethiopia)",
        "domain": "addisstandard.com",
        "feed_url": "https://addisstandard.com/feed/",
        "source_type": "rss",
        "country": "ET",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },
    {
        "id": "src-allafrica-latest",
        "name": "AllAfrica News Service",
        "domain": "allafrica.com",
        "feed_url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",
        "source_type": "rss",
        "country": "ZA",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },

    # ==========================================
    # Latin America & Caribbean (Local & Regional)
    # ==========================================
    {
        "id": "src-batimes-ar",
        "name": "Buenos Aires Times (Argentina)",
        "domain": "batimes.com.ar",
        "feed_url": "https://www.batimes.com.ar/feed",
        "source_type": "rss",
        "country": "AR",
        "language": "en",
        "reliability_score": 0.84,
        "active": True
    },
    {
        "id": "src-riotimes-br",
        "name": "The Rio Times (Brazil)",
        "domain": "riotimesonline.com",
        "feed_url": "https://www.riotimesonline.com/feed/",
        "source_type": "rss",
        "country": "BR",
        "language": "en",
        "reliability_score": 0.83,
        "active": True
    },
    {
        "id": "src-mexiconewsdaily-mx",
        "name": "Mexico News Daily",
        "domain": "mexiconewsdaily.com",
        "feed_url": "https://mexiconewsdaily.com/feed/",
        "source_type": "rss",
        "country": "MX",
        "language": "en",
        "reliability_score": 0.83,
        "active": True
    },
    {
        "id": "src-bogotapost-co",
        "name": "The Bogota Post (Colombia)",
        "domain": "thebogotapost.com",
        "feed_url": "https://thebogotapost.com/feed/",
        "source_type": "rss",
        "country": "CO",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },
    {
        "id": "src-santiagotimes-cl",
        "name": "The Santiago Times (Chile)",
        "domain": "santiagotimes.cl",
        "feed_url": "https://santiagotimes.cl/feed/",
        "source_type": "rss",
        "country": "CL",
        "language": "en",
        "reliability_score": 0.82,
        "active": True
    },
    {
        "id": "src-jamaicagleaner-jm",
        "name": "Jamaica Gleaner (Caribbean)",
        "domain": "jamaica-gleaner.com",
        "feed_url": "https://jamaica-gleaner.com/feed/rss.xml",
        "source_type": "rss",
        "country": "JM",
        "language": "en",
        "reliability_score": 0.85,
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

    # ==========================================
    # Europe (Local, Regional & Eastern/Northern)
    # ==========================================
    {
        "id": "src-kyivindependent-ua",
        "name": "The Kyiv Independent (Ukraine)",
        "domain": "kyivindependent.com",
        "feed_url": "https://kyivindependent.com/feed/",
        "source_type": "rss",
        "country": "UA",
        "language": "en",
        "reliability_score": 0.89,
        "active": True
    },
    {
        "id": "src-notesfrompoland-pl",
        "name": "Notes from Poland",
        "domain": "notesfrompoland.com",
        "feed_url": "https://notesfrompoland.com/feed/",
        "source_type": "rss",
        "country": "PL",
        "language": "en",
        "reliability_score": 0.87,
        "active": True
    },
    {
        "id": "src-baltictimes-lv",
        "name": "The Baltic Times (Baltics)",
        "domain": "baltictimes.com",
        "feed_url": "https://www.baltictimes.com/rss/",
        "source_type": "rss",
        "country": "LV",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-kathimerini-gr",
        "name": "Kathimerini English (Greece)",
        "domain": "ekathimerini.com",
        "feed_url": "https://www.ekathimerini.com/rss/",
        "source_type": "rss",
        "country": "GR",
        "language": "en",
        "reliability_score": 0.86,
        "active": True
    },
    {
        "id": "src-icelandreview-is",
        "name": "Iceland Review",
        "domain": "icelandreview.com",
        "feed_url": "https://www.icelandreview.com/feed/",
        "source_type": "rss",
        "country": "IS",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },
    {
        "id": "src-highnorthnews-no",
        "name": "High North News (Arctic)",
        "domain": "highnorthnews.com",
        "feed_url": "https://www.highnorthnews.com/en/rss.xml",
        "source_type": "rss",
        "country": "NO",
        "language": "en",
        "reliability_score": 0.87,
        "active": True
    },
    {
        "id": "src-dw-world",
        "name": "Deutsche Welle",
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
        "name": "The Guardian",
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
        "name": "Euronews Europe",
        "domain": "euronews.com",
        "feed_url": "https://www.euronews.com/rss?format=mrss&level=theme&name=news",
        "source_type": "rss",
        "country": "FR",
        "language": "en",
        "reliability_score": 0.85,
        "active": True
    },

    # ==========================================
    # Oceania & Pacific (Local & Regional)
    # ==========================================
    {
        "id": "src-rnz-nz",
        "name": "Radio New Zealand (RNZ)",
        "domain": "rnz.co.nz",
        "feed_url": "https://www.rnz.co.nz/rss/national.xml",
        "source_type": "rss",
        "country": "NZ",
        "language": "en",
        "reliability_score": 0.90,
        "active": True
    },
    {
        "id": "src-abc-au-world",
        "name": "ABC News Australia",
        "domain": "abc.net.au",
        "feed_url": "https://www.abc.net.au/news/feed/52278/rss.xml",
        "source_type": "rss",
        "country": "AU",
        "language": "en",
        "reliability_score": 0.90,
        "active": True
    },
    {
        "id": "src-islandsbusiness-fj",
        "name": "Islands Business (Pacific)",
        "domain": "islandsbusiness.com",
        "feed_url": "https://islandsbusiness.com/feed/",
        "source_type": "rss",
        "country": "FJ",
        "language": "en",
        "reliability_score": 0.83,
        "active": True
    },

    # ==========================================
    # North America
    # ==========================================
    {
        "id": "src-cbc-world",
        "name": "CBC News Canada",
        "domain": "cbc.ca",
        "feed_url": "https://www.cbc.ca/cmlink/rss-world",
        "source_type": "rss",
        "country": "CA",
        "language": "en",
        "reliability_score": 0.91,
        "active": True
    },
    {
        "id": "src-npr-world",
        "name": "NPR News",
        "domain": "npr.org",
        "feed_url": "https://feeds.npr.org/1004/rss.xml",
        "source_type": "rss",
        "country": "US",
        "language": "en",
        "reliability_score": 0.90,
        "active": True
    }
]
