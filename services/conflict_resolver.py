# services/conflict_resolver.py

from typing import List
from models.resolved_claims import ResolvedClaim
from models.evidence_models import Evidence

class ConflictResolver:
    """
    Resolves contradictory claims using weighted, explainable rules.
    """

    def resolve(self, claims: List[ResolvedClaim]) -> List[ResolvedClaim]:
        resolved = []

        grouped = self._group_by_type(claims)

        for claim_type, group in grouped.items():
            resolved.extend(self._resolve_claim_type(claim_type, group))

        return resolved

    def _group_by_type(self, claims):
        groups = {}
        for c in claims:
            groups.setdefault(c.claim_type, []).append(c)
        return groups

    def _resolve_claim_type(self, claim_type, claims):
        if claim_type in {"IS_PEP", "IS_SANCTIONED"}:
            return [self._resolve_boolean(claim_type, claims)]

        if claim_type == "PEP_ROLE":
            return self._resolve_roles(claims)

        return claims

    def _resolve_boolean(self, claim_type, claims):
        score = 0.0
        sources = []
        evidences = []

        for c in claims:
            direction = 1 if c.claim_value.lower() == "true" else -1
            score += direction * c.confidence
            sources.extend(c.sources)
            evidences.extend(c.evidences)

        resolved_value = "true" if score > 0 else "false"
        confidence = round(abs(score) / len(claims), 2)

        return ResolvedClaim(
            claim_type=claim_type,
            claim_value=resolved_value,
            confidence=confidence,
            sources=list(set(sources)),
            evidences=evidences,
        )

    def _resolve_roles(self, claims):
        """
        Multiple roles can coexist.
        Conflicts resolved via authority + confidence.
        """
        claims.sort(key=lambda c: c.confidence, reverse=True)
        return claims
