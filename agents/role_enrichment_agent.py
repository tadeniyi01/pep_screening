# agents/role_enrichment_agent.py

from agents.role_discovery.wikidata_role_source import WikidataRoleSource
from agents.role_discovery.news_role_source import NewsRoleSource
from agents.role_discovery.registry_role_source import RegistryRoleSource
from agents.role_resolution_agent import RoleResolutionAgent
from agents.role_normalization import RoleNormalizer
from services.news.provider_registry import ProviderRegistry
from models.role_models import DiscoveredRole
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class RoleEnrichmentAgent:
    """
    Aggregates roles from multiple sources:
    - Structured sources: Wikidata, Registry
    - Media sources: News (RSS, GNews)
    Implements normalization, temporal decay, PEP boosting, and field-level provenance.
    """

    TEMPORAL_DECAY_YEARS = 3  # News older than this has confidence decay

    HIGH_RISK_TITLES = {"President", "Prime Minister", "Head of State"}

    def __init__(self, news_provider_registry: ProviderRegistry | None = None):
        self.news_provider_registry = news_provider_registry
        self.sources = [
            WikidataRoleSource(),
            RegistryRoleSource(),
        ]
        if self.news_provider_registry:
            self.sources.append(NewsRoleSource(self.news_provider_registry))

        self.resolver = RoleResolutionAgent()
        self.normalizer = RoleNormalizer()

    async def enrich(self, name: str, country: str) -> dict:
        roles: list[DiscoveredRole] = []
        source_map: dict[str, str] = {}
        evidence = {"dob": None, "state": None, "aliases": [], "images": []}

        # ---------- Primary sources ----------
        for source in self.sources:
            try:
                fetched = await source.fetch(name, country)

                # --- Handle Wikidata field-level evidence ---
                # Some sources may return a tuple: (roles, life_status) or dict with roles/evidence
                if isinstance(fetched, tuple):
                    # WikidataRoleSource returns (List[DiscoveredRole], life_status)
                    fetched_roles, life_status = fetched
                    evidence["dob"] = evidence["dob"] or None  # keep from elsewhere if needed
                    fetched_roles = fetched_roles or []
                elif isinstance(fetched, dict) and "roles" in fetched:
                    fetched_roles = fetched.get("roles", [])
                    ev = fetched.get("evidence", {})
                    evidence["dob"] = evidence["dob"] or ev.get("date_of_birth")
                    evidence["state"] = evidence["state"] or ev.get("state")
                    evidence["aliases"].extend(ev.get("aliases", []))
                    evidence["images"].extend(ev.get("images", []))
                elif isinstance(fetched, list):
                    fetched_roles = fetched
                else:
                    fetched_roles = []

                # --- Normalize roles and adjust confidence ---
                for r in fetched_roles:
                    if not isinstance(r, DiscoveredRole):
                        logger.warning(
                            "[RoleEnrichment] Skipping invalid role object from %s: %s",
                            source.__class__.__name__,
                            type(r),
                        )
                        continue

                    r.title = self.normalizer.normalize_title(r.title)
                    r.organisation = self.normalizer.normalize_org(r.organisation)
                    r.source_detail = f"{r.source} ({source.__class__.__name__})"

                    # Temporal decay for old news
                    if getattr(r, "start_year", None) and source.__class__.__name__.startswith("News"):
                        age = datetime.now().year - r.start_year
                        if age > self.TEMPORAL_DECAY_YEARS:
                            decay_factor = max(0.1, 1.0 - (age - self.TEMPORAL_DECAY_YEARS) * 0.1)
                            r.confidence *= decay_factor

                    # PEP boosting for high-risk roles from Wikidata
                    if r.title in self.HIGH_RISK_TITLES and source.__class__.__name__ == "WikidataRoleSource":
                        r.confidence = max(r.confidence, 0.95)

                    key = f"{r.title} ({r.organisation})"
                    source_map[key] = r.source_detail

                # --- Flatten fetched_roles into main list ---
                roles.extend(fetched_roles)

                logger.info(
                    "[RoleEnrichment] %d roles fetched from %s for %s, %s",
                    len(fetched_roles),
                    source.__class__.__name__,
                    name,
                    country,
                )

            except Exception as e:
                logger.warning(
                    "[ROLE SOURCE ERROR] %s: %s",
                    source.__class__.__name__,
                    e,
                )

        # ---------- Resolve duplicates / conflicts ----------
        resolved_roles = self.resolver.resolve(roles)

        # Attach source info for audit trace
        for r in resolved_roles:
            key = f"{r.title} ({r.organisation})"
            r.source_detail = source_map.get(key, r.source)

        logger.info(
            "[RoleEnrichment] Total resolved roles for %s, %s: %d",
            name,
            country,
            len(resolved_roles),
        )

        return {
            "roles": resolved_roles,
            "evidence": evidence,
        }

