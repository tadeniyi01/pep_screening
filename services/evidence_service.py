# services/evidence_service.py
from typing import List
from models.media_models import MediaItem
from services.news.provider_registry import ProviderRegistry

class EvidenceService:
    """
    Unified access layer for fetching and tagging evidence from all sources.
    """

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry

    async def fetch(
        self,
        query: str,
        country: str = "",
        start_date=None,
        end_date=None
    ) -> List[MediaItem]:
        """
        Fetch all evidence from providers in the registry.
        """
        return await self.registry.fetch_all(
            query=query,
            country=country,
            start_date=start_date,
            end_date=end_date
        )
