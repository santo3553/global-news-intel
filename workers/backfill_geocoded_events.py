"""
Worldwide Geocoding Backfill Script for Global News Intelligence.
Iterates through all events and articles in global_news.db,
extracts location, city, country, and precise verified coordinates
using the offline gazetteer and source country metadata.
"""

import os
import sys
import sqlite3
from typing import Dict

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.extraction.geocoder import Geocoder, ISO_TO_COUNTRY

def backfill_events_geocoding(db_path: str = "global_news.db"):
    print(f"--> Starting global geocoding backfill on {db_path}...")
    geocoder = Geocoder()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all events with their associated articles and sources
    cursor.execute("""
        SELECT e.id, e.canonical_title, e.summary, e.city, e.country, e.latitude, e.longitude
        FROM events e
    """)
    events = cursor.fetchall()
    total_events = len(events)
    print(f"--> Total events in DB: {total_events}")

    updated_count = 0
    country_counts: Dict[str, int] = {}

    for evt_id, title, summary, current_city, current_country, lat, lng in events:
        # Check if event already has a valid country and coordinates
        has_valid_country = bool(current_country and current_country.strip() and current_country != "None")
        has_valid_coords = bool(lat and lng and (lat != 0.0 or lng != 0.0))

        # Fetch linked articles and sources for this event
        cursor.execute("""
            SELECT a.title, a.cleaned_content, s.country, s.name, s.domain
            FROM event_articles ea
            JOIN articles a ON ea.article_id = a.id
            JOIN sources s ON a.source_id = s.id
            WHERE ea.event_id = ?
        """, (evt_id,))
        articles = cursor.fetchall()

        # Build context from event title, summary, and article snippets
        source_country_hints = []
        article_texts = []
        for a_title, a_content, s_country, s_name, s_domain in articles:
            if s_country and s_country != "UN":
                source_country_hints.append(s_country)
            article_texts.append(f"{a_title or ''} {(a_content or '')[:300]}")

        primary_source_hint = source_country_hints[0] if source_country_hints else None
        combined_text = f"{title or ''} {summary or ''} {' '.join(article_texts[:3])}"

        # Resolve location using Geocoder
        loc = geocoder.resolve(
            raw_name=current_city or "",
            country_hint=current_country or primary_source_hint,
            text_context=combined_text
        )

        # If country was resolved or can be updated
        if loc.country:
            new_country = loc.country
            new_city = loc.city or current_city
            new_region = loc.admin_region
            new_lat = loc.latitude if loc.latitude != 0.0 else lat
            new_lng = loc.longitude if loc.longitude != 0.0 else lng
            new_conf = loc.location_confidence

            cursor.execute("""
                UPDATE events
                SET country = ?, city = ?, admin_region = COALESCE(?, admin_region),
                    latitude = ?, longitude = ?, location_confidence = ?
                WHERE id = ?
            """, (new_country, new_city, new_region, new_lat, new_lng, new_conf, evt_id))

            updated_count += 1
            country_counts[new_country] = country_counts.get(new_country, 0) + 1
        elif has_valid_country:
            country_counts[current_country] = country_counts.get(current_country, 0) + 1

    conn.commit()

    # Check overall database country distribution after backfill
    cursor.execute("""
        SELECT country, count(*)
        FROM events
        GROUP BY country
        ORDER BY count(*) DESC
    """)
    final_distribution = cursor.fetchall()
    conn.close()

    print(f"\n--> [BACKFILL COMPLETED] Successfully updated {updated_count} events.")
    print("--> Final Event Distribution by Country:")
    for country, count in final_distribution:
        print(f"    - {country or 'Global / Unspecified'}: {count} events")

if __name__ == "__main__":
    backfill_events_geocoding()
