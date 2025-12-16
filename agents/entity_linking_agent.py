from difflib import SequenceMatcher
from typing import List
from models.pep_models import EntityLinkResult


class EntityLinkingAgent:
    def similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def link(
        self,
        query_name: str,
        candidate_name: str,
        query_country: str,
        candidate_country: str,
        query_positions: List[str],
        candidate_positions: List[str],
        query_org: str,
        candidate_org: str,
        source_credibility: float = 1.0
    ) -> EntityLinkResult:

        confidence = 0.0
        signals = []

        # 1. Name similarity
        name_score = self.similarity(query_name, candidate_name)
        confidence += name_score * 0.35
        signals.append(f"Name similarity: {round(name_score,2)}")

        # 2. Country match
        if query_country and candidate_country:
            if query_country == candidate_country:
                confidence += 0.20
                signals.append("Country match")

        # 3. Position overlap
        if set(query_positions) & set(candidate_positions):
            confidence += 0.20
            signals.append("Position match")

        # 4. Organization match
        if query_org and candidate_org and query_org == candidate_org:
            confidence += 0.15
            signals.append("Organization match")

        # 5. Source credibility
        confidence += source_credibility * 0.10
        signals.append(f"Source credibility: {source_credibility}")

        return EntityLinkResult(
            confidence=round(confidence, 2),
            signals=signals
        )
