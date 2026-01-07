from dotenv import load_dotenv
import os
from typing import List

# Load .env as early as possible
load_dotenv(override=True)


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_list_env(name: str) -> List[str]:
    raw = get_env(name)
    if not raw:
        return []
    
    # Filter out dead or blocked feeds
    blocked = [
        "reuters.com/rssFeed",
        "vanguardngr.com/feed",
        "pmnewsnigeria.com/feed",
        "dailynigerian.com/feed",
        "pulse.ng/news/rss"
    ]
    
    feeds = [x.strip() for x in raw.split(",") if x.strip()]
    return [f for f in feeds if not any(b in f for b in blocked)]


# ---------- API Keys ----------
GROQ_API_KEY = get_env("GROQ_API_KEY")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
GNEWS_API_KEY = get_env("GNEWS_API_KEY")
OPENSANCTIONS_API_KEY = get_env("OPENSANCTIONS_API_KEY")

# ---------- Feeds ----------
RSS_FEEDS = get_list_env("RSS_FEEDS")

