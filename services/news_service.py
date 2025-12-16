# services/news_service.py

from models.media_models import MediaItem
from typing import List, Optional
import json
from pathlib import Path


class NewsService:
    def __init__(self):
        data_path = Path("data/mock_news.json")
        self.data = json.loads(data_path.read_text())

    def fetch(
        self,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[MediaItem]:
        """
        Fetch news articles mentioning the name.
        Date filtering is optional (prototype-safe).
        """

        results = []

        for item in self.data:
            if name.lower() in item["headline"].lower():
                results.append(MediaItem(**item))

        return results
