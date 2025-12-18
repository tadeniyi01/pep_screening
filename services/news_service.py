import logging
from typing import List, Optional

from models.media_models import MediaItem
from services.news.provider_registry import ProviderRegistry
from utils.url_utils import extract_domain

logger = logging.getLogger(__name__)


class NewsService:
    """
    Aggregates multiple news providers and returns
    de-duplicated adverse media articles.
    """

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    def fetch(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[MediaItem]:
        """
        Fetch news articles related to a query string.

        Args:
            query: Person or entity name
            start_date: Optional ISO date (YYYY-MM-DD)
            end_date: Optional ISO date (YYYY-MM-DD)

        Returns:
            De-duplicated list of MediaItem objects
        """
        if not query or not query.strip():
            return []

        articles: List[MediaItem] = []

        for provider in self.registry.active_providers():
            try:
                # Providers currently only accept `query`
                provider_items = provider.fetch(query)
                articles.extend(provider_items)

            except Exception as e:
                logger.warning(
                    "News provider '%s' failed for query '%s': %s",
                    provider.name,
                    query,
                    str(e),
                    exc_info=True,
                )

        return self._deduplicate(articles)

    def _deduplicate(self, items: List[MediaItem]) -> List[MediaItem]:
        """
        Remove duplicate articles based on headline + date + source domain.
        """
        seen = set()
        unique: List[MediaItem] = []

        for item in items:
            key = (
                item.headline.lower().strip(),
                item.date,
                extract_domain(item.source),
            )

            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique
