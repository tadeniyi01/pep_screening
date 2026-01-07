# services/evidence_registry.py

from collections import defaultdict
from typing import List, Tuple
from models.evidence_models import Evidence
from models.resolved_claims import ResolvedClaim
from models.evidence_registry_models import EvidenceRegistryResult

class UnifiedEvidenceRegistry:
    """
    Aggregates, deduplicates, and resolves evidence across sources.
    """

    def register(self, evidences: List[Evidence]) -> EvidenceRegistryResult:
        grouped = defaultdict(list)

        # --- Group evidence by claim ---
        for ev in evidences:
            key = self._group_key(ev)
            grouped[key].append(ev)

        resolved_claims: List[ResolvedClaim] = []

        for (_, claim_value), items in grouped.items():
            resolved_claims.append(self._resolve_group(items))

        return EvidenceRegistryResult(resolved_claims=resolved_claims)

    def _group_key(self, ev: Evidence) -> Tuple[str, str]:
        return (ev.claim_type, ev.claim_value)

    def _resolve_group(self, evidences: List[Evidence]) -> ResolvedClaim:
        sources = list({e.source for e in evidences})

        # Weighted confidence aggregation
        weighted_sum = sum(e.confidence * e.source_weight for e in evidences)
        weight_total = sum(e.source_weight for e in evidences)

        confidence = round(weighted_sum / weight_total, 2) if weight_total else 0.0

        start_dates = [e.start_date for e in evidences if e.start_date]
        end_dates = [e.end_date for e in evidences if e.end_date]

        return ResolvedClaim(
            claim_type=evidences[0].claim_type,
            claim_value=evidences[0].claim_value,
            confidence=confidence,
            sources=sources,
            evidences=evidences,
            start_date=min(start_dates) if start_dates else None,
            end_date=max(end_dates) if end_dates else None,
        )
