# agents/role_enrichment/role_enricher.py

from typing import List
from models.role_models import DiscoveredRole
from services.role_enrichment.wikidata_role_service import WikidataRoleService


class RoleEnricher:
    def __init__(self):
        self.wikidata = WikidataRoleService()

    def enrich(self, name: str, country: str) -> List[DiscoveredRole]:
        roles: List[DiscoveredRole] = []

        # --- Wikidata (authoritative) ---
        try:
            roles.extend(
                self.wikidata.fetch_roles(name, country)
            )
        except Exception as e:
            # IMPORTANT: never crash screening because of enrichment
            print(f"[WARN] Wikidata role fetch failed: {e}")

        return roles
