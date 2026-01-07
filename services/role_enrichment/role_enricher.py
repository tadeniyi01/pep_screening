# from typing import List
# from services.role_enrichment.wikidata_role_service import WikidataRoleService
# from services.role_enrichment.news_role_service import NewsRoleService
# from services.role_enrichment.registry_role_service import NigeriaRegistryRoleService
# from services.role_enrichment.llm_role_service import LLMRoleService
# from models.role_models import DiscoveredRole


# class RoleEnricher:
#     def __init__(self):
#         self.wikidata = WikidataRoleService()
#         self.news = NewsRoleService()
#         self.registry = NigeriaRegistryRoleService()
#         self.llm = LLMRoleService()

#     def enrich(self, name: str, country: str) -> List[DiscoveredRole]:
#         roles = []

#         roles.extend(self.wikidata.fetch_roles(name, "Q1033"))  # Nigeria
#         roles.extend(self.registry.fetch_roles(name))
#         roles.extend(self.news.extract_roles(name))
#         roles.extend(self.llm.infer_roles(name, country))

#         return roles
