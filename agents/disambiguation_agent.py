from typing import Dict
from difflib import SequenceMatcher


class DisambiguationAgent:
    """
    Determines whether a candidate entity matches the query person.
    """

    def name_similarity(self, query: str, candidate: str) -> float:
        return SequenceMatcher(None, query.lower(), candidate.lower()).ratio()

    def disambiguate(
        self,
        query_name: str,
        candidate_name: str,
        candidate_country: str,
        query_country: str,
    ) -> Dict:
        score = 0.0
        reasons = []

        # Name similarity (primary signal)
        name_score = self.name_similarity(query_name, candidate_name)
        score += name_score * 0.6
        reasons.append(f"Name similarity score: {round(name_score, 2)}")

        # Country match (hard filter)
        if query_country and candidate_country:
            if query_country == candidate_country:
                score += 0.3
                reasons.append("Country match")
            else:
                reasons.append("Country mismatch")
                return {
                    "match": False,
                    "confidence": 0.0,
                    "reasons": reasons
                }

        # Final decision
        match = score >= 0.7

        return {
            "match": match,
            "confidence": round(score, 2),
            "reasons": reasons
        }
