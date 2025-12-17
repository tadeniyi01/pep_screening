import json
from typing import List
from services.llm_service import LLMService
from models.role_models import DiscoveredRole


class LLMRoleService:
    def __init__(self, llm: LLMService):
        self.llm = llm

    def fetch_roles(self, name: str, country: str) -> List[DiscoveredRole]:
        prompt = f"""
        Identify all public or political offices held by {name} in {country}.
        Return JSON array with fields:
        title, organisation, start_year, end_year
        """

        raw = self.llm.generate(prompt)

        try:
            data = json.loads(raw)
        except Exception:
            return []

        roles = []
        for item in data:
            roles.append(
                DiscoveredRole(
                    title=item["title"],
                    organisation=item["organisation"],
                    country=country,
                    start_year=item.get("start_year"),
                    end_year=item.get("end_year"),
                    source="LLM",
                    confidence=0.55
                )
            )

        return roles
