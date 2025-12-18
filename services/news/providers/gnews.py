import requests
from typing import List
from models.media_models import MediaItem
from services.news.providers.base import NewsProvider


class GNewsProvider(NewsProvider):
    name = "gnews"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key.strip() if api_key else None
        self.url = "https://gnews.io/api/v4/search"
        self.enabled = bool(self.api_key)

    def fetch(self, query: str) -> List[MediaItem]:
        # Gracefully disable provider if no API key
        if not self.enabled:
            return []

        params = {
            "q": f'"{query}"',
            "lang": "en",
            "max": 20,
            "apikey": self.api_key,
        }

        try:
            response = requests.get(self.url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception:
            # Never crash the pipeline on provider failure
            return []

        items: List[MediaItem] = []

        for article in data.get("articles", []):
            items.append(
                MediaItem(
                    date=article.get("publishedAt", "")[:10],
                    source=article.get("source", {}).get("url", ""),
                    headline=article.get("title", ""),
                    excerpt=article.get("description") or "",
                    score=65.0,
                    inferring="Negative",
                    tags=[],
                    language="en",
                    persons=[query],
                    organizations=[],
                    country=""
                )
            )

        return items
