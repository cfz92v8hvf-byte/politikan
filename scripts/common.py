import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def env(name: str, default: str = "") -> str:
    values = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return os.getenv(name, values.get(name, default))


def settings() -> dict:
    return json.loads((ROOT / "config" / "settings.json").read_text(encoding="utf-8"))
