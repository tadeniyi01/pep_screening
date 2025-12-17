import json
import requests
from typing import List
from models.role_models import DiscoveredRole


class NewsRoleSource:
    """
    Extracts public roles from news coverage (GDELT).
    This is a supporting source — not authoritative.
    """

    SOURCE = "News"
    BASE_CONFIDENCE = 0.65

    ROLE_KEYWORDS = {
        "president": "President",
        "governor": "Governor",
        "senator": "Senator",
        "minister": "Minister",
        "vice president": "Vice President",
        "lawmaker": "Lawmaker",
        "chairman": "Chairman",
    }

    def fetch(self, name: str, country: str) -> List[DiscoveredRole]:
        params = {
            "query": name,
            "mode": "ArtList",
            "maxrecords": 50,
            "format": "json",
        }

        try:
            response = requests.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params=params,
                timeout=20,
            )
            response.raise_for_status()
        except Exception as e:
            print(f"[ROLE SOURCE ERROR] NewsRoleSource: {e}")
            return []

        data = response.json()
        articles = data.get("articles", [])

        roles: List[DiscoveredRole] = []

        for article in articles:
            title = article.get("title", "") or ""
            snippet = article.get("snippet", "") or ""
            text = f"{title} {snippet}".lower()

            for keyword, normalized_title in self.ROLE_KEYWORDS.items():
                if keyword in text:
                    roles.append(
                        DiscoveredRole(
                            title=normalized_title,
                            organisation=self._infer_org(normalized_title, country),
                            country=country,
                            start_year=None,
                            end_year=None,
                            source=self.SOURCE,
                            confidence=self.BASE_CONFIDENCE,
                            raw_reference=json.dumps({
                                "source": "GDELT",
                                "title": title,
                                "url": article.get("url"),
                                "keyword": keyword,
                            }),
                        )
                    )

        return roles

    def _infer_org(self, title: str, country: str) -> str:
        """
        Conservative organisation inference.
        """
        if country == "NG":
            if title == "President":
                return "Federal Republic of Nigeria"
            if title == "Governor":
                return "State Government of Nigeria"
        return ""
