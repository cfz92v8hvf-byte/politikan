#!/usr/bin/env python3
"""Generate a small public editorial dashboard from the saved queue."""
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from storage import connect
from common import ROOT


def main():
    db = connect()
    rows = [dict(row) for row in db.execute(
        "SELECT id, source, source_url, title_ru, status, published_to_telegram_at "
        "FROM posts ORDER BY id DESC LIMIT 60"
    )]
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "queue.json").write_text(
        json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(), "posts": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    items = []
    labels = {"pending": "Ожидает", "approved": "Одобрено", "published": "Опубликовано", "rejected": "Отклонено", "expired": "Снято: устарело"}
    for row in rows:
        status = html.escape(labels.get(row["status"], row["status"]))
        title = html.escape(row["title_ru"])
        source = html.escape(row["source"])
        url = html.escape(row["source_url"], quote=True)
        items.append(f'<article class="post {row["status"]}"><span>{status}</span><h2>{title}</h2><p>{source} · <a href="{url}" target="_blank" rel="noreferrer">первоисточник</a></p></article>')

    page = f'''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Политикан — очередь</title>
<style>body{{margin:0;background:#071328;color:#edf3ff;font:16px system-ui,-apple-system,sans-serif}}main{{max-width:760px;margin:auto;padding:40px 20px}}h1{{margin:0 0 8px}}.note{{color:#9cb0d0;margin-bottom:28px}}article{{padding:18px;border:1px solid #1e3960;border-radius:14px;margin:12px 0;background:#0c1d38}}h2{{font-size:18px;margin:10px 0}}p{{margin:0;color:#a9bbd7}}a{{color:#79b5ff}}span{{font-size:12px;padding:4px 9px;border-radius:20px;background:#254d7d}}.published span{{background:#22633b}}.pending span{{background:#765719}}.rejected{{opacity:.55}}</style>
<main><h1>🇪🇺 Политикан</h1><p class="note">Очередь европейских новостей · обновляется каждый час</p>{''.join(items) or '<p>Очередь пока пуста.</p>'}</main></html>'''
    (docs / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
