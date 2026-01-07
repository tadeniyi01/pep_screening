# agents/role_discovery/wikidata_role_source.py
from typing import List, Tuple, Optional
from models.role_models import DiscoveredRole
import httpx, json, logging
from datetime import datetime
from agents.role_normalization import RoleNormalizer

logger = logging.getLogger(__name__)

class WikidataRoleSource:
    SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

    HIGH_RISK_TITLES = {"President", "Head of State", "Prime Minister"}

    def __init__(self):
        self.normalizer = RoleNormalizer()

    async def fetch(self, name: str, country: str = "") -> Tuple[List[DiscoveredRole], Optional[str]]:
        if not name:
            return [], None

        query = f"""
        SELECT ?person ?personLabel ?positionLabel ?start ?end ?orgLabel ?countryLabel WHERE {{
          ?person wdt:P31 wd:Q5;
                  rdfs:label "{name}"@en;
                  wdt:P39 ?position .
          OPTIONAL {{ ?position p:P580 ?startStmt . ?startStmt ps:P580 ?start. }}
          OPTIONAL {{ ?position p:P582 ?endStmt . ?endStmt ps:P582 ?end. }}
          OPTIONAL {{ ?position wdt:P279 ?org. }}
          OPTIONAL {{ ?person wdt:P27 ?country. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "PEPScreeningBot/1.0 (https://github.com/example/pep-screening; pep-screening@example.com)"
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.SPARQL_ENDPOINT, params={"query": query}, headers=headers, timeout=10)
                resp.raise_for_status()
                results = resp.json().get("results", {}).get("bindings", [])
        except Exception as e:
            logger.warning(f"[Wikidata ERROR] Failed to fetch roles for '{name}': {e}")
            return [], None

        roles: List[DiscoveredRole] = []

        for row in results:
            raw_title = row.get("positionLabel", {}).get("value")
            raw_org = row.get("orgLabel", {}).get("value") or row.get("countryLabel", {}).get("value") or ""
            start = row.get("start", {}).get("value")
            end = row.get("end", {}).get("value")
            country_code = country.upper() if country else ""

            if not raw_title:
                continue

            title = self.normalizer.normalize_title(raw_title)
            org = self.normalizer.normalize_org(raw_org)

            confidence = 0.9
            if title in self.HIGH_RISK_TITLES:
                confidence = 1.0

            start_year = int(start[:4]) if start else None
            end_year = int(end[:4]) if end else None

            roles.append(
                DiscoveredRole(
                    title=title,
                    organisation=org,
                    country=country_code,
                    start_year=start_year,
                    end_year=end_year,
                    source="Wikidata",
                    confidence=confidence,
                    raw_reference=json.dumps(row)
                )
            )

        logger.info(f"[Wikidata] Fetched {len(roles)} roles for '{name}'")

        # --- Optional Life Status ---
        life_status = None
        if results:
            person_uri = results[0]["person"]["value"]
            life_status = await self._fetch_life_status(person_uri)

        return roles, life_status

    async def _fetch_life_status(self, person_uri: str) -> Optional[str]:
        """
        Uses Wikidata P570 (date of death) to determine alive/deceased.
        Returns 'Alive' or 'Deceased'.
        """
        query = f"""
        SELECT ?dob ?dod WHERE {{
          <{person_uri}> wdt:P569 ?dob .
          OPTIONAL {{ <{person_uri}> wdt:P570 ?dod. }}
        }}
        """
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "PEPScreeningBot/1.0 (https://github.com/example/pep-screening; pep-screening@example.com)"
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.SPARQL_ENDPOINT, params={"query": query}, headers=headers, timeout=10)
                resp.raise_for_status()
                results = resp.json().get("results", {}).get("bindings", [])
                if results:
                    dod = results[0].get("dod", {}).get("value")
                    return "Deceased" if dod else "Alive"
        except Exception as e:
            logger.warning(f"[Wikidata ERROR] Failed to fetch life status for '{person_uri}': {e}")
        return None
