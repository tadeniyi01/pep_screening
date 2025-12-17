# agents/role_discovery/wikidata_role_source.py
from models.role_models import DiscoveredRole

class WikidataRoleSource:
    def fetch(self, name: str, country: str) -> list[DiscoveredRole]:
        # later: SPARQL
        if name.lower() == "bola ahmed tinubu":
            return [
                DiscoveredRole(
                    title="President",
                    organisation="Federal Republic of Nigeria",
                    country="NG",
                    start_year=2023,
                    source="Wikidata",
                    confidence=0.95
                ),
                DiscoveredRole(
                    title="Governor",
                    organisation="Lagos State Government",
                    country="NG",
                    start_year=1999,
                    end_year=2007,
                    source="Wikidata",
                    confidence=0.9
                )
            ]
        return []
