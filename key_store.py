"""Resolve and persist the user's Gemini API key.

Resolution order:
1. GEMINI_API_KEY environment variable (includes values loaded from a dev .env).
2. %APPDATA%\\CVmate\\config.json written by the first-run dialog.

The dialog saves the key to config.json so packaged-app users never have to
touch a terminal or edit a .env file.
"""

import json
import os
from pathlib import Path

_CONFIG_DIR = Path(os.getenv("APPDATA") or Path.home()) / "CVmate"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


def get_api_key():
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    try:
        data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    key = data.get("GEMINI_API_KEY")
    return key.strip() if key and key.strip() else None


def save_api_key(key: str) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(
        json.dumps({"GEMINI_API_KEY": key.strip()}), encoding="utf-8"
    )


def config_path() -> str:
    return str(_CONFIG_FILE)


if __name__ == "__main__":
    print(f"Config file: {config_path()}")
    print("Key present:", bool(get_api_key()))
