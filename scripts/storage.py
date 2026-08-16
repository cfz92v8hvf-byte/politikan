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
