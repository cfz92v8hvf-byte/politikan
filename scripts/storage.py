import sqlite3
from pathlib import Path
from common import ROOT

DB = ROOT / "data" / "politikan.sqlite3"


def connect():
    DB.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS posts (
      id INTEGER PRIMARY KEY, source TEXT NOT NULL, source_url TEXT UNIQUE NOT NULL,
      published_at TEXT, original_title TEXT NOT NULL, title_ru TEXT NOT NULL,
      summary_ru TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, published_to_telegram_at TEXT
    )""")
    return db


def is_seen(db, url, title):
    row = db.execute("SELECT 1 FROM posts WHERE source_url = ? OR original_title = ?", (url, title)).fetchone()
    return row is not None


def claim_collection_slot(db, min_interval_minutes: int) -> bool:
    """Allow at most one collection cycle during the configured interval.

    GitHub's scheduled jobs are best-effort and can occasionally be delayed.
    The workflow may therefore request a few backup starts per hour; this small
    SQLite lease makes those starts safe without increasing publication volume.
    """
    db.execute("""CREATE TABLE IF NOT EXISTS operations (
      name TEXT PRIMARY KEY, last_started_at TEXT NOT NULL
    )""")
    cursor = db.execute(
        """INSERT INTO operations (name, last_started_at) VALUES ('collect', CURRENT_TIMESTAMP)
        ON CONFLICT(name) DO UPDATE SET last_started_at=CURRENT_TIMESTAMP
        WHERE datetime(operations.last_started_at) <= datetime('now', ?)""",
        (f"-{min_interval_minutes} minutes",),
    )
    db.commit()
    return cursor.rowcount == 1
