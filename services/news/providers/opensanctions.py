# services/news/providers/opensanctions.py

import httpx
from typing import List, Optional
from datetime import date

from models.media_models import MediaItem
from services.news.base_provider import BaseProvider


class OpenSanctionsProvider(BaseProvider):
    """
    OpenSanctions structured PEP / sanctions provider.
    Requires API key.
    """
    name = "OpenSanctions"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.base_url = "https://www.opensanctions.org/api/entities/"

    async def fetch(
        self,
        query: str,
        country: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[MediaItem]:

        if not self.api_key:
            print("[OpenSanctions] Skipped: no API key configured")
            return []

        headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Accept": "application/json",
        }

        params = {
            "q": query,
            "limit": 20,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=15.0,
                )
                if response.status_code == 404:
                    print(f"[OpenSanctions] No entity found for '{query}'")
                    return []
                response.raise_for_status()
                payload = response.json()

        except Exception as e:
            print(f"[OpenSanctions ERROR] {e}")
            return []

        results = payload.get("results", [])
        items: List[MediaItem] = []

        for entity in results:
            caption = entity.get("caption")
            if not caption:
                continue

            countries = entity.get("countries", [])
            country_code = countries[0] if countries else ""

            items.append(
                MediaItem(
                    date=str(date.today()),
                    source="OpenSanctions",
                    headline=f"{caption} listed in OpenSanctions",
                    excerpt=(
                        "Entity matched against OpenSanctions datasets, "
                        "including sanctions and politically exposed persons."
                    ),
                    score=90.0,  # Structured source → high base score
                    inferring="Neutral",
                    tags=["sanctions", "pep", "structured"],
                    persons=[caption],
                    organizations=[],
                    country=country_code,
                    credibility_score=0.95,
                    entity_link_confidence=0.90,
                )
            )

        print(f"[OpenSanctions] fetched {len(items)} items for '{query}'")
        return items
