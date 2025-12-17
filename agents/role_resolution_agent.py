from collections import defaultdict
from agents.role_normalization import RoleNormalizer
from models.role_models import DiscoveredRole


class RoleResolutionAgent:
    def __init__(self):
        self.normalizer = RoleNormalizer()

    def resolve(self, roles: list[DiscoveredRole]) -> list[DiscoveredRole]:
        grouped = defaultdict(list)

        for role in roles:
            canonical_title = self.normalizer.normalize_title(role.title)
            canonical_org = self.normalizer.normalize_org(role.organisation)

            key = (
                canonical_title,
                canonical_org,
                role.country
            )

            grouped[key].append(role)

        resolved_roles = []

        for (title, org, country), group in grouped.items():
            resolved_roles.append(
                self._merge_group(
                    title, org, country, group
                )
            )

        return resolved_roles

    def _merge_group(
        self,
        title: str,
        org: str,
        country: str,
        group: list[DiscoveredRole]
    ) -> DiscoveredRole:
        confidence = max(r.confidence for r in group)

        start_year = min(
            (r.start_year for r in group if r.start_year),
            default=None
        )
        end_year = max(
            (r.end_year for r in group if r.end_year),
            default=None
        )

        sources = sorted({r.source for r in group})

        return DiscoveredRole(
            title=title,
            organisation=org,
            country=country,
            start_year=start_year,
            end_year=end_year,
            source="+".join(sources),
            confidence=confidence,
            raw_reference=None
        )
