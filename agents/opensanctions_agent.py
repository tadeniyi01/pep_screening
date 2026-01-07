# agents/opensanctions_agent.py

from services.intelligence.opensanctions_service import OpenSanctionsService
from services.intelligence.opensanctions_mapper import map_opensanctions_to_evidence
from typing import List
from models.evidence_models import Evidence

class OpenSanctionsAgent:
    def __init__(self):
        self.service = OpenSanctionsService()

    def extract(self, name: str) -> List[Evidence]:
        entities = self.service.search(name)
        return map_opensanctions_to_evidence(entities)
