#!/usr/bin/env python3
import argparse
import email.utils
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Optional
from storage import connect, is_seen
from common import settings
from translator import translate, TranslationError
from telegram import publish


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(value or ""))).strip()


def entry_date(entry) -> Optional[datetime]:
    raw = entry.findtext("pubDate") or entry.findtext("{http://purl.org/dc/elements/1.1/}date") or entry.findtext("updated")
    if not raw:
        return None
    try:
        return email.utils.parsedate_to_datetime(raw).astimezone(timezone.utc)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None


def read_feed(source):
    request = urllib.request.Request(source["feed"], headers={"User-Agent": "PolitikanRSS/0.1 (+editorial news digest)"})
    with urllib.request.urlopen(request, timeout=25) as response:
        root = ET.fromstring(response.read())
    for entry in root.findall(".//item") + root.findall(".//{http://www.w3.org/2005/Atom}entry"):
        title = clean(entry.findtext("title") or entry.findtext("{http://www.w3.org/2005/Atom}title"))
        link = entry.findtext("link") or ""
        atom_link = entry.find("{http://www.w3.org/2005/Atom}link")
        if atom_link is not None:
            link = atom_link.attrib.get("href", link)
        summary = clean(entry.findtext("description") or entry.findtext("summary") or entry.findtext("{http://www.w3.org/2005/Atom}summary"))
        if title and link:
            yield title, link, summary, entry_date(entry)


def is_relevant(title, summary, keywords):
    haystack = f"{title} {summary}".casefold()
    return any(keyword.casefold() in haystack for keyword in keywords)


def collect():
    config, db = settings(), connect()
    newest = datetime.now(timezone.utc) - timedelta(hours=config["max_age_hours"])
    added = 0
    for source in config["sources"]:
        if not source.get("enabled"):
            continue
        try:
            for title, url, summary, published in read_feed(source):
                if added >= config["max_items_per_run"]:
                    break
                if (published and published < newest) or is_seen(db, url, title):
                    continue
                if not is_relevant(title, summary, config.get("topic_keywords", [])):
                    continue
                try:
                    title_ru, summary_ru = translate(title), translate(summary or title)
                except TranslationError as exc:
                    print(f"Skipped translation: {title[:60]} ({exc})")
                    continue
                db.execute("INSERT INTO posts (source, source_url, published_at, original_title, title_ru, summary_ru) VALUES (?, ?, ?, ?, ?, ?)",
                           (source["name"], url, published.isoformat() if published else None, title, title_ru, summary_ru))
                db.commit()
                added += 1
        except Exception as exc:
            print(f"Source failed {source['name']}: {exc}")
    print(f"Added to queue: {added}")
    if config["mode"] == "auto":
        publish_ready(db, include_pending=True, limit=config.get("max_publish_per_run", 4), max_age_hours=config.get("pending_max_age_hours", 3))


def publish_ready(db, include_pending=False, limit=4, max_age_hours=3):
    # A channel is useful for fresh information, not a delayed backlog.
    db.execute(
        "UPDATE posts SET status='expired' WHERE status IN ('pending', 'approved') "
        "AND datetime(COALESCE(published_at, created_at)) < datetime('now', ?)",
        (f'-{max_age_hours} hours',),
    )
    db.commit()
    statuses = "('approved', 'pending')" if include_pending else "('approved')"
    for post in db.execute(f"SELECT * FROM posts WHERE status IN {statuses} ORDER BY COALESCE(published_at, created_at) DESC LIMIT ?", (limit,)):
        try:
            publish(post)
            db.execute("UPDATE posts SET status='published', published_to_telegram_at=CURRENT_TIMESTAMP WHERE id=?", (post["id"],))
            db.commit()
            print(f"Published #{post['id']}")
        except Exception as exc:
            print(f"Publish failed #{post['id']}: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish-approved", action="store_true")
    args = parser.parse_args()
    if args.publish_approved:
        config = settings()
        publish_ready(connect(), limit=config.get("max_publish_per_run", 4), max_age_hours=config.get("pending_max_age_hours", 3))
    else:
        collect()
