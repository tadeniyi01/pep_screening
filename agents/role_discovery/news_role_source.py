# agents/role_discovery/news_role_source.py
from typing import List
from models.role_models import DiscoveredRole
from services.news.provider_registry import ProviderRegistry

class NewsRoleSource:
    """
    Role source that fetches potential roles from news providers
    registered in the ProviderRegistry.
    """
    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    async def fetch(self, name: str, country: str) -> List[DiscoveredRole]:
        roles: List[DiscoveredRole] = []

        for provider in self.registry.providers:
            try:
                # Try passing country only if provider supports it
                fetch_method = getattr(provider, "fetch")
                if "country" in fetch_method.__code__.co_varnames:
                    items = await fetch_method(name, country=country)
                else:
                    items = await fetch_method(name)
                for item in items:
                    # Map headline/entity info into a DiscoveredRole
                    roles.append(
                        DiscoveredRole(
                            title=item.headline or "Public Office Holder",
                            organisation=item.organizations[0] if item.organizations else "",
                            country=item.country or country,
                            start_year=None,  # News roles rarely have exact years
                            end_year=None,
                            source=provider.name,
                            confidence=0.5  # Default medium confidence for news evidence
                        )
                    )
            except Exception as e:
                print(f"[NewsRoleSource ERROR] {provider.name}: {e}")

        return roles
