import sqlite3
import re
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


_TITLE_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on",
    "or", "the", "to", "with", "will", "says", "say", "said", "news", "live", "latest", "video", "report",
}


def _title_terms(title: str) -> set[str]:
    terms = set()
    for word in re.findall(r"[a-z0-9]+", (title or "").casefold()):
        if word.endswith("ing") and len(word) > 5:
            word = word[:-3]
        elif word.endswith("ed") and len(word) > 4:
            word = word[:-2]
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]
        if len(word) > 2 and word not in _TITLE_STOPWORDS:
            terms.add(word)
    return terms


def is_semantic_duplicate(db, title: str, max_age_hours: int) -> bool:
    """Conservatively suppress a recent report of the same event from another source."""
    candidate = _title_terms(title)
    if len(candidate) < 4:
        return False
    rows = db.execute(
        "SELECT original_title FROM posts WHERE status IN ('pending', 'approved', 'published') "
        "AND datetime(created_at) >= datetime('now', ?)",
        (f"-{max_age_hours} hours",),
    )
    for row in rows:
        existing = _title_terms(row["original_title"])
        common = candidate & existing
        union = candidate | existing
        if len(common) >= 4 and len(common) / len(union) >= 0.45:
            return True
    return False


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
