import json
import urllib.parse
import urllib.request
from common import env


def publish(post) -> None:
    token, channel = env("TELEGRAM_BOT_TOKEN"), env("TELEGRAM_CHANNEL")
    if not token or not channel:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL must be configured")
    message = format_post(post)
    payload = urllib.parse.urlencode({"chat_id": channel, "text": message, "parse_mode": "HTML", "disable_web_page_preview": "false"}).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(urllib.request.Request(url, data=payload), timeout=20) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError(result)


def html(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_post(post) -> str:
    """Keep every item scannable, visually distinct, and linked to its source."""
    return (
        "🇪🇺 <b>{source}</b> <i>· европейская повестка</i>\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "<b>{title}</b>\n\n"
        "{summary}\n\n"
        "<blockquote>Оригинал: {original}</blockquote>\n\n"
        "🔗 <a href=\"{url}\">Читать первоисточник</a>"
    ).format(
        source=html(post["source"]),
        title=html(post["title_ru"]),
        summary=html(post["summary_ru"]),
        original=html(post["original_title"]),
        url=html(post["source_url"]),
    )
