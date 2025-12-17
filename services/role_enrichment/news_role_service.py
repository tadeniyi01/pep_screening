from typing import List
from models.role_models import DiscoveredRole
from services.news_service import NewsService


class NewsRoleService:
    BASE_CONFIDENCE = 0.65

    def __init__(self):
        self.news = NewsService()

    def extract_roles(self, name: str) -> List[DiscoveredRole]:
        articles = self.news.fetch(name)
        roles = []

        for article in articles:
            for role in self._extract_role_from_text(article.headline):
                roles.append(
                    DiscoveredRole(
                        title=role,
                        organisation=article.source,
                        country=article.country,
                        source="news",
                        confidence=self.BASE_CONFIDENCE
                    )
                )

        return roles

    def _extract_role_from_text(self, text: str) -> List[str]:
        KNOWN_ROLES = [
            "President",
            "Governor",
            "Senator",
            "Minister",
            "Commissioner",
            "Chairman"
        ]

        return [r for r in KNOWN_ROLES if r.lower() in text.lower()]
