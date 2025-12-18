import json
from pathlib import Path
from typing import List
from models.media_models import MediaItem
from .base import NewsProvider


class MockNewsProvider(NewsProvider):
    name = "mock"

    def __init__(self, path: str = "data/mock_news.json"):
        self.data = json.loads(Path(path).read_text())

    def fetch(self, query: str) -> List[MediaItem]:
        results = []
        for item in self.data:
            if query.lower() in item["headline"].lower():
                results.append(MediaItem(**item))
        return results
