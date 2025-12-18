import feedparser
from typing import List
from models.media_models import MediaItem
from services.news.providers.base import NewsProvider


class RSSProvider(NewsProvider):
    name = "rss"

    def __init__(self, feeds: List[str]):
        if not feeds:
            raise ValueError("RSSProvider requires at least one feed URL")
        self.feeds = feeds

    def fetch(self, query: str) -> List[MediaItem]:
        items: List[MediaItem] = []

        for feed_url in self.feeds:
            feed = feedparser.parse(feed_url)

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
                        inferring="Negative",
                        tags=[],
                        language="en",
                        persons=[query],
                        organizations=[],
                        country=""
                    )
                )

        return items
