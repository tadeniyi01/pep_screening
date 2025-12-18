from services.news.provider_registry import ProviderRegistry
from services.news.providers.rss import RSSProvider
from services.news.providers.gnews import GNewsProvider
from config.settings import RSS_FEEDS, GNEWS_API_KEY


def build_provider_registry() -> ProviderRegistry:
    providers = []

    if RSS_FEEDS:
        providers.append(RSSProvider(RSS_FEEDS))

    if GNEWS_API_KEY:
        providers.append(GNewsProvider(GNEWS_API_KEY))

    return ProviderRegistry(providers)
