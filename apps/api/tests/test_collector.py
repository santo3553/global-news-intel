import pytest
from workers.collector.rss_collector import parse_feed_xml


RSS_20_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <channel>
        <title>Reuters World News</title>
        <link>https://www.reuters.com</link>
        <description>Reuters World News Feed</description>
        <item>
            <title>Magnitude 7.1 earthquake strikes southern Japan</title>
            <link>https://www.reuters.com/world/japan-quake-2026?utm_source=feed</link>
            <description>A major earthquake struck southern Japan on Monday.</description>
            <pubDate>Mon, 14 Sep 2026 08:30:00 GMT</pubDate>
            <dc:creator>John Doe</dc:creator>
        </item>
        <item>
            <title>UN climate summit concludes with global agreement</title>
            <link>https://www.reuters.com/world/climate-summit-accord</link>
            <description>Delegates agreed to accelerated emissions reduction benchmarks.</description>
            <pubDate>Mon, 14 Sep 2026 07:15:00 GMT</pubDate>
        </item>
    </channel>
</rss>
"""

ATOM_FIXTURE = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Global Dispatch</title>
    <link href="https://example.org/"/>
    <updated>2026-09-14T10:00:00Z</updated>
    <entry>
        <title>Webb Telescope discovers atmosphere on Earth-sized exoplanet</title>
        <link href="https://example.org/entry-1" rel="alternate"/>
        <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
        <published>2026-09-14T09:45:00Z</published>
        <summary>Spectroscopic data confirms non-primordial atmosphere.</summary>
        <author>
            <name>Dr. Jane Smith</name>
        </author>
    </entry>
</feed>
"""


def test_parse_feed_xml_rss20():
    items = parse_feed_xml(RSS_20_FIXTURE)
    assert len(items) == 2
    assert items[0].title == "Magnitude 7.1 earthquake strikes southern Japan"
    assert "reuters.com/world/japan-quake-2026" in items[0].link
    assert items[0].author == "John Doe"
    assert "A major earthquake struck" in items[0].summary
    assert items[1].title == "UN climate summit concludes with global agreement"


def test_parse_feed_xml_atom():
    items = parse_feed_xml(ATOM_FIXTURE)
    assert len(items) == 1
    assert items[0].title == "Webb Telescope discovers atmosphere on Earth-sized exoplanet"
    assert items[0].link == "https://example.org/entry-1"
    assert items[0].author == "Dr. Jane Smith"
    assert "Spectroscopic data confirms" in items[0].summary


def test_parse_feed_xml_malformed_graceful():
    bad_xml = "<rss><channel><item><title>Unclosed tag</item></rss>"
    items = parse_feed_xml(bad_xml)
    assert items == []
