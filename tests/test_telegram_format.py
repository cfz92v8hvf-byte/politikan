import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from telegram import format_post


def test_post_format_has_clear_editorial_sections():
    post = {
        "source": "Euronews",
        "title_ru": "Заголовок на русском",
        "summary_ru": "Краткая суть новости.",
        "original_title": "Original English headline",
        "source_url": "https://example.com/story",
    }
    rendered = format_post(post)
    assert "🇪🇺 <b>Euronews</b>" in rendered
    assert "Оригинал: Original English headline" in rendered
    assert "Читать первоисточник" in rendered
