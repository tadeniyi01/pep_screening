from agents.role_discovery.wikidata_role_source import WikidataRoleSource
from agents.role_discovery.llm_role_source import LLMRoleSource
from agents.role_discovery.news_role_source import NewsRoleSource
from agents.role_discovery.registry_role_source import RegistryRoleSource
from agents.role_resolution_agent import RoleResolutionAgent
from services.llm_service import LLMService


class RoleEnrichmentAgent:
    def __init__(self, llm_service: LLMService | None = None):
        self.sources = [
            WikidataRoleSource(),
            RegistryRoleSource(),
            NewsRoleSource(),
        ]

        if llm_service:
            self.sources.append(LLMRoleSource(llm_service))

        self.resolver = RoleResolutionAgent()


    def enrich(self, name: str, country: str):
        roles = []

        for source in self.sources:
            try:
                roles.extend(source.fetch(name, country))
            except Exception as e:
                print(f"[ROLE SOURCE ERROR] {source.__class__.__name__}: {e}")

        return self.resolver.resolve(roles)
