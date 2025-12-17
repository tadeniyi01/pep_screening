from collections import defaultdict
from typing import List
from models.role_models import DiscoveredRole
from utils.source_weights import SOURCE_WEIGHTS


class RoleConfidenceAggregator:
    """
    Aggregates role confidence using Bayesian OR fusion.
    """

    def aggregate(self, roles: List[DiscoveredRole]) -> List[DiscoveredRole]:
        grouped = self._group_roles(roles)
        aggregated: List[DiscoveredRole] = []

        for group in grouped.values():
            if len(group) == 1:
                aggregated.append(group[0])
                continue

            confidence = self._bayesian_or(group)

            # Pick most authoritative role as base
            base = max(
                group,
                key=lambda r: SOURCE_WEIGHTS.get(r.source, 0.5)
            )

            aggregated.append(
                DiscoveredRole(
                    title=base.title,
                    organisation=base.organisation,
                    country=base.country,
                    start_year=base.start_year,
                    end_year=base.end_year,
                    source="+".join(sorted({r.source for r in group})),
                    confidence=round(min(confidence, 0.99), 3),
                    raw_reference=base.raw_reference,
                )
            )

        return aggregated

    def _bayesian_or(self, roles: List[DiscoveredRole]) -> float:
        """
        P(role) = 1 - Π (1 - weight * confidence)
        """
        product = 1.0

        for role in roles:
            weight = SOURCE_WEIGHTS.get(role.source, 0.5)
            adjusted = min(role.confidence * weight, 0.99)
            product *= (1 - adjusted)

        return 1 - product

    def _group_roles(self, roles: List[DiscoveredRole]):
        """
        Groups semantically identical roles.
        """
        groups = defaultdict(list)

        for r in roles:
            key = (
                r.title.lower().strip(),
                r.organisation.lower().strip(),
                r.country,
                r.start_year,
                r.end_year,
            )
            groups[key].append(r)

        return groups
