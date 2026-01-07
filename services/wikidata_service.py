import requests
import logging
from schemas.pep_response import LifeStatusSchema

logger = logging.getLogger(__name__)

WIKIDATA_API = "https://www.wikidata.org/w/api.php"


def fetch_life_status(name: str) -> LifeStatusSchema | None:
    """
    Returns LifeStatusSchema from Wikidata if found.
    """
    try:
        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "limit": 1,
        }

        res = requests.get(WIKIDATA_API, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        if not data.get("search"):
            return None

        entity_id = data["search"][0]["id"]

        entity_res = requests.get(
            WIKIDATA_API,
            params={
                "action": "wbgetentities",
                "ids": entity_id,
                "props": "claims",
                "format": "json",
            },
            timeout=10,
        )
        entity_res.raise_for_status()
        entity = entity_res.json()["entities"][entity_id]

        claims = entity.get("claims", {})

        # Date of death → P570
        if "P570" in claims:
            death_time = claims["P570"][0]["mainsnak"]["datavalue"]["value"]["time"]
            date_of_death = death_time.replace("+", "")[:10]
            return LifeStatusSchema(
                status="Deceased",
                date_of_death=date_of_death,
            )

        # No P570 = alive (for humans)
        return LifeStatusSchema(status="Alive", date_of_death="")

    except Exception as e:
        logger.warning("Wikidata life status fetch failed for %s: %s", name, e)
        return None
