"""Resolve and persist the Gemini API key in the project's .env file."""

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"


def get_api_key() -> str | None:
    val = os.getenv("GEMINI_API_KEY")
    return val.strip() if val and val.strip() else None


def save_api_key(key: str) -> None:
    key = key.strip()
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    out, replaced = [], False
    for line in lines:
        if line.strip().split("=", 1)[0].strip() == "GEMINI_API_KEY":
            out.append(f"GEMINI_API_KEY={key}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"GEMINI_API_KEY={key}")
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    os.environ["GEMINI_API_KEY"] = key


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(override=True)
    print(f".env path: {ENV_PATH}")
    print(f"API key set: {get_api_key() is not None}")
