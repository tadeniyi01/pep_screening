# services/intelligence/opensanctions_service.py

import requests
from typing import List
from models.opensanctions_models import OpenSanctionsEntity, OpenSanctionsPosition

class OpenSanctionsService:
    BASE_URL = "https://api.opensanctions.org/match"

    def search(self, name: str) -> List[OpenSanctionsEntity]:
        payload = {
            "queries": {
                "q1": {
                    "schema": "Person",
                    "properties": {
                        "name": [name]
                    }
                }
            }
        }

        response = requests.post(self.BASE_URL, json=payload, timeout=15)
        response.raise_for_status()

        data = response.json()
        results = []

        for match in data.get("responses", {}).get("q1", {}).get("results", []):
            entity = match.get("entity", {})

            positions = []
            for pos in entity.get("position", []):
                positions.append(
                    OpenSanctionsPosition(
                        title=pos.get("name"),
                        start_date=pos.get("startDate"),
                        end_date=pos.get("endDate"),
                    )
                )

            results.append(
                OpenSanctionsEntity(
                    name=entity.get("name"),
                    score=match.get("score", 0.0),
                    datasets=entity.get("datasets", []),
                    positions=positions,
                    topics=entity.get("topics", []),
                    entity_id=entity.get("id"),
                )
            )

        return results
