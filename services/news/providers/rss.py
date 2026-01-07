# services/news/providers/rss.py
import feedparser
import httpx
from typing import List
from models.media_models import MediaItem
from services.news.providers.base import NewsProvider

class RSSProvider(NewsProvider):
    name = "rss"

    def __init__(self, feeds: List[str]):
        if not feeds:
            raise ValueError("RSSProvider requires at least one feed URL")
        self.feeds = feeds

    async def fetch(self, query: str) -> List[MediaItem]:
        items: List[MediaItem] = []

        for feed_url in self.feeds:
            try:
                # Fetch asynchronously
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*"
                }
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(feed_url, headers=headers, timeout=10.0)
                    if response.status_code != 200:
                        print(f"[RSS SKIP] {feed_url} returned {response.status_code}")
                        continue
                    content = response.content
                
                # Parse content
                feed = feedparser.parse(content)

                for entry in feed.entries:
                    if query.lower() not in entry.title.lower():
                        continue

                    items.append(
                        MediaItem(
                            date=entry.get("published", "")[:10],
                            source=feed_url,
                            headline=entry.title,
                            excerpt=entry.get("summary", "")[:300],
                            score=60.0,
                            inferring="Neutral",
                            tags=[],
                            language="en",
                            persons=[query],
                            organizations=[],
                            country=""
                        )
                    )
            except Exception as e:
                print(f"[RSS ERROR] Failed to fetch/parse {feed_url}: {e}")
                continue

        return items
