#!/usr/bin/env python3
import argparse
from storage import connect

db = connect()
parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["list", "approve", "reject"])
parser.add_argument("id", nargs="?", type=int)
args = parser.parse_args()

if args.action == "list":
    for post in db.execute("SELECT id, status, source, title_ru, source_url FROM posts WHERE status != 'published' ORDER BY id"):
        print(f"#{post['id']} [{post['status']}] {post['source']}: {post['title_ru']}\n{post['source_url']}\n")
else:
    if args.id is None:
        parser.error("id is required")
    status = "approved" if args.action == "approve" else "rejected"
    db.execute("UPDATE posts SET status=? WHERE id=? AND status='pending'", (status, args.id))
    db.commit()
    print(f"Post #{args.id}: {status}")
