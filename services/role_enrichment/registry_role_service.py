from typing import List
from models.role_models import DiscoveredRole


class NigeriaRegistryRoleService:
    BASE_CONFIDENCE = 0.90

    def fetch_roles(self, name: str) -> List[DiscoveredRole]:
        # Prototype: stubbed registry data
        # Later: CAC API, INEC scrape, official PDFs

        if "Tinubu" not in name:
            return []

        return [
            DiscoveredRole(
                title="President of Nigeria",
                organisation="Government of Nigeria",
                country="Nigeria",
                source="nigeria_registry",
                confidence=self.BASE_CONFIDENCE
            )
        ]
