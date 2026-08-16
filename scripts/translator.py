import json
import urllib.parse
import urllib.request
from common import env


class TranslationError(Exception):
    pass


def translate(text: str) -> str:
    url = env("TRANSLATOR_URL")
    if not url:
        return translate_mymemory(text)
    payload = {"q": text, "source": "auto", "target": "ru", "format": "text"}
    key = env("TRANSLATOR_API_KEY")
    if key:
        payload["api_key"] = key
    request = urllib.request.Request(
        url.rstrip("/") + "/translate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "PolitikanBot/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.load(response)
        return result["translatedText"].strip()
    except Exception as exc:
        raise TranslationError(str(exc)) from exc


def translate_mymemory(text: str) -> str:
    """Free fallback for the reviewed MVP; keep posts short to respect its quota."""
    query = urllib.parse.urlencode({"q": text, "langpair": "en|ru"})
    request = urllib.request.Request(
        "https://api.mymemory.translated.net/get?" + query,
        headers={"User-Agent": "PolitikanBot/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.load(response)
        translated = result.get("responseData", {}).get("translatedText", "").strip()
        if not translated:
            raise ValueError("empty translation")
        return translated
    except Exception as exc:
        raise TranslationError(str(exc)) from exc
