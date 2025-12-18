from dotenv import load_dotenv
import os
from typing import List

# Load .env as early as possible
load_dotenv()


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_list_env(name: str) -> List[str]:
    raw = get_env(name)
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


# ---------- API Keys ----------
GROQ_API_KEY = get_env("GROQ_API_KEY")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
GNEWS_API_KEY = get_env("GNEWS_API_KEY")

# ---------- Feeds ----------
RSS_FEEDS = get_list_env("RSS_FEEDS")

