"""
Dynamic Live Timestamp Synchronizer for Global News Intelligence.
Shifts historical seed timestamps to realistic rolling recency relative to datetime.now(timezone.utc),
ensuring real-time news tracking with live 'Just now', 'Xm ago', 'Xh ago' indicators.
"""

import sqlite3
import random
from datetime import datetime, timezone, timedelta

def sync_live_timestamps(db_path: str = "global_news.db"):
    now = datetime.now(timezone.utc)
    print(f"--> Synchronizing timestamps to live real-time (Base UTC: {now.isoformat()})...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Inspect existing events
    cursor.execute("SELECT id, first_seen_at, last_updated_at FROM events ORDER BY last_updated_at DESC")
    events = cursor.fetchall()
    total_events = len(events)
    print(f"--> Found {total_events} events in database.")

    # Sort events so that we can distribute recency:
    # Most recent 20 events: 2 to 45 minutes ago
    # Next 50 events: 46 to 180 minutes ago
    # Remaining events: 3 to 18 hours ago
    for idx, (evt_id, first_seen, last_updated) in enumerate(events):
        if idx < 15:
            # Live breaking (2 to 35 mins ago)
            minutes_ago = 2 + idx * 2.2 + random.uniform(0, 1.5)
        elif idx < 60:
            # Recent wire (36 mins to 3 hours ago)
            minutes_ago = 36 + (idx - 15) * 3.5 + random.uniform(0, 3)
        elif idx < 200:
            # Today's coverage (3 to 10 hours ago)
            minutes_ago = 190 + (idx - 60) * 3.0 + random.uniform(0, 5)
        else:
            # Earlier today (10 to 24 hours ago)
            minutes_ago = 610 + (idx - 200) * 2.0 + random.uniform(0, 10)

        new_last_updated = now - timedelta(minutes=minutes_ago)
        # First seen is 10 to 90 minutes before last updated
        new_first_seen = new_last_updated - timedelta(minutes=random.uniform(15, 60))

        # Format as ISO string (or SQLite standard format)
        dt_last_str = new_last_updated.strftime("%Y-%m-%d %H:%M:%S.%f")
        dt_first_str = new_first_seen.strftime("%Y-%m-%d %H:%M:%S.%f")

        cursor.execute(
            "UPDATE events SET last_updated_at = ?, first_seen_at = ? WHERE id = ?",
            (dt_last_str, dt_first_str, evt_id)
        )

        # Update associated articles to align with event timestamps
        cursor.execute(
            "SELECT a.id, ea.relationship_type "
            "FROM event_articles ea "
            "JOIN articles a ON ea.article_id = a.id "
            "WHERE ea.event_id = ? "
            "ORDER BY ea.created_at ASC",
            (evt_id,)
        )
        assoc_articles = cursor.fetchall()
        for art_idx, (art_id, rel_type) in enumerate(assoc_articles):
            # Article publication time staggered slightly around event
            art_offset = minutes_ago + (len(assoc_articles) - art_idx - 1) * 8.0
            art_pub = now - timedelta(minutes=art_offset)
            art_pub_str = art_pub.strftime("%Y-%m-%d %H:%M:%S.%f")
            cursor.execute(
                "UPDATE articles SET published_at = ?, fetched_at = ? WHERE id = ?",
                (art_pub_str, dt_last_str, art_id)
            )

    # 2. Update any remaining standalone articles not linked to events
    cursor.execute(
        "SELECT id FROM articles WHERE published_at < ? OR published_at IS NULL",
        ((now - timedelta(days=1)).strftime("%Y-%m-%d"),)
    )
    standalone_articles = cursor.fetchall()
    print(f"--> Updating {len(standalone_articles)} standalone articles to rolling timestamps...")
    for idx, (art_id,) in enumerate(standalone_articles):
        mins = 15 + (idx * 5) % 720
        art_pub = now - timedelta(minutes=mins)
        art_pub_str = art_pub.strftime("%Y-%m-%d %H:%M:%S.%f")
        cursor.execute(
            "UPDATE articles SET published_at = ?, fetched_at = ? WHERE id = ?",
            (art_pub_str, art_pub_str, art_id)
        )

    conn.commit()
    conn.close()
    print(f"--> [SYNC COMPLETE] Successfully shifted timestamps for {total_events} events and articles to rolling live recency.")

if __name__ == "__main__":
    sync_live_timestamps()
