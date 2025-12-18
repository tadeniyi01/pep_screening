from typing import List
from services.news.providers.base import NewsProvider


class ProviderRegistry:
    """
    Central registry for all active news providers.
    """

    def __init__(self):
        self._providers: List[NewsProvider] = []

    def register(self, provider: NewsProvider) -> None:
        self._providers.append(provider)

    def active_providers(self) -> List[NewsProvider]:
        return self._providers.copy()
