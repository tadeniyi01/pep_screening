# import requests
# from typing import List, Optional

# from models.role_models import DiscoveredRole

# WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"


# class WikidataRoleService:
#     SOURCE = "Wikidata"
#     BASE_CONFIDENCE = 0.85

#     def fetch_roles(self, name: str, country: str) -> List[DiscoveredRole]:
#         person_qid = self._resolve_person_qid(name)

#         if not person_qid:
#             return []

#         return self._fetch_roles_by_qid(person_qid, country)

#     # -------------------------------------------------
#     # PHASE 1: PERSON RESOLUTION (NO COUNTRY FILTER)
#     # -------------------------------------------------

#     def _resolve_person_qid(self, name: str) -> Optional[str]:
#         query = f"""
#         PREFIX wd: <http://www.wikidata.org/entity/>
#         PREFIX wdt: <http://www.wikidata.org/prop/direct/>
#         PREFIX p: <http://www.wikidata.org/prop/>
#         PREFIX ps: <http://www.wikidata.org/prop/statement/>
#         PREFIX wikibase: <http://wikiba.se/ontology#>
#         PREFIX bd: <http://www.bigdata.com/rdf#>
#         PREFIX mwapi: <https://www.mediawiki.org/ontology#API/>
    
#         SELECT DISTINCT ?person WHERE {{
#           SERVICE wikibase:mwapi {{
#             bd:serviceParam wikibase:endpoint "www.wikidata.org";
#                              wikibase:api "EntitySearch";
#                              mwapi:search "{name}";
#                              mwapi:language "en";
#                              mwapi:limit 20.
#             ?person wikibase:apiOutputItem mwapi:item.
#           }}
    
#           ?person wdt:P31 wd:Q5.       # must be human
#           ?person p:P39 ?statement.    # must have held office
#           ?statement ps:P39 ?position.
#         }}
#         LIMIT 1
#         """
    
#         response = requests.get(
#             WIKIDATA_ENDPOINT,
#             params={"query": query},
#             headers={
#                 "Accept": "application/sparql+json",
#                 "User-Agent": "PEP-Screening/1.0",
#             },
#             timeout=30,
#         )
#         response.raise_for_status()
    
#         bindings = response.json()["results"]["bindings"]
#         if not bindings:
#             return None
    
#         return bindings[0]["person"]["value"].split("/")[-1]
#     # -------------------------------------------------
#     # PHASE 2: ROLE EXTRACTION
#     # -------------------------------------------------

#     def _fetch_roles_by_qid(self, qid: str, country: str) -> List[DiscoveredRole]:
#         query = f"""
#         PREFIX wd: <http://www.wikidata.org/entity/>
#         PREFIX wdt: <http://www.wikidata.org/prop/direct/>
#         PREFIX p: <http://www.wikidata.org/prop/>
#         PREFIX ps: <http://www.wikidata.org/prop/statement/>
#         PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
#         PREFIX wikibase: <http://wikiba.se/ontology#>
#         PREFIX bd: <http://www.bigdata.com/rdf#>

#         SELECT DISTINCT
#           ?positionLabel
#           ?orgLabel
#           ?start
#           ?end
#         WHERE {{
#           wd:{qid} p:P39 ?statement.
#           ?statement ps:P39 ?position.

#           OPTIONAL {{ ?statement pq:P580 ?start. }}
#           OPTIONAL {{ ?statement pq:P582 ?end. }}
#           OPTIONAL {{ ?statement pq:P642 ?org. }}

#           SERVICE wikibase:label {{
#             bd:serviceParam wikibase:language "en".
#           }}
#         }}
#         """

#         response = requests.get(
#             WIKIDATA_ENDPOINT,
#             params={"query": query},
#             headers={"Accept": "application/sparql+json"},
#             timeout=30,
#         )
#         response.raise_for_status()

#         roles: List[DiscoveredRole] = []

#         for row in response.json()["results"]["bindings"]:
#             roles.append(
#                 DiscoveredRole(
#                     title=row["positionLabel"]["value"],
#                     organisation=row.get("orgLabel", {}).get("value", ""),
#                     country=country,
#                     start_year=self._parse_year(row.get("start")),
#                     end_year=self._parse_year(row.get("end")),
#                     source=self.SOURCE,
#                     confidence=self.BASE_CONFIDENCE,
#                 )
#             )

#         return roles

#     @staticmethod
#     def _parse_year(value: Optional[dict]) -> Optional[int]:
#         if not value:
#             return None
#         try:
#             return int(value["value"][:4])
#         except Exception:
#             return None
