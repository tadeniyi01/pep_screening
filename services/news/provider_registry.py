import inspect
import asyncio
import logging
from typing import List, Dict, Type
from services.news.base_provider import BaseProvider

logger = logging.getLogger(__name__)

class ProviderRegistry:
    """
    Unified registry of news and structured data providers.
    Handles registration, fetching, and cross-provider orchestration.
    """

    def __init__(self, providers: List[BaseProvider] = None):
        self.providers: List[BaseProvider] = providers or []

    def register(self, provider: BaseProvider):
        if not any(p.name == provider.name for p in self.providers):
            self.providers.append(provider)

    async def fetch_all(
        self,
        query: str,
        country: str = "",
        start_date=None,
        end_date=None
    ) -> List:
        """
        Fetches evidence from all providers in parallel, respecting their signatures.
        """
        all_items = []
        
        # Create coroutines for all providers dynamically
        tasks = []
        for provider in self.providers:
            try:
                sig = inspect.signature(provider.fetch)
                kwargs = {}
                
                # Check for optional args in signature
                if "country" in sig.parameters:
                    kwargs["country"] = country
                if "start_date" in sig.parameters:
                    kwargs["start_date"] = start_date
                if "end_date" in sig.parameters:
                    kwargs["end_date"] = end_date
                
                tasks.append(provider.fetch(query, **kwargs))
            except Exception as e:
                # If inspect fails or something else
                logger.error(f"[ProviderRegistry Error] Preparing fetch for {provider.name}: {e}")

        # Run in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for provider, result in zip(self.providers, results):
            if isinstance(result, Exception):
                # Fail gracefully if a provider errors
                logger.exception(f"Error fetching from {provider.name}", exc_info=result)
                continue
            
            # Post-process items
            for item in result:
                if provider.name in ["EveryPolitician", "OpenSanctions"]:
                    item.evidence_type = "structured_pep"
                else:
                    item.evidence_type = "adverse_media"
            
            all_items.extend(result)

        return all_items
