# agents/adverse_media_agent.py

from models.media_models import AdverseMediaResult
from utils.scoring import calculate_weighted_score, derive_risk_status
from utils.source_registry import SOURCE_CREDIBILITY
from utils.url_utils import extract_domain
from agents.reasoning_agent import ReasoningAgent
from agents.disambiguation_agent import DisambiguationAgent
from agents.entity_linking_agent import EntityLinkingAgent
from services.news_service import NewsService
from typing import Optional


class AdverseMediaAgent:
    def __init__(self):
        self.news = NewsService()
        self.reasoning = ReasoningAgent()
        self.disambiguator = DisambiguationAgent()
        self.entity_linker = EntityLinkingAgent()

    def analyze(
        self,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> AdverseMediaResult:
        """
        Analyze adverse media for a subject.
        Supports optional date filtering.
        """

        articles = self.news.fetch(
            name=name,
            start_date=start_date,
            end_date=end_date
        )

        linked = []

        for item in articles:
            if not item.persons:
                continue

            # --- Source credibility weighting ---
            domain = extract_domain(item.source)
            credibility = SOURCE_CREDIBILITY.get(domain, 0.5)
            item.credibility_score = credibility

            # --- Entity linking ---
            link = self.entity_linker.link(
                query_name=name,
                candidate_name=item.persons[0],
                query_country="",
                candidate_country=item.country,
                query_positions=[],
                candidate_positions=[],
                query_org="",
                candidate_org="",
                source_credibility=credibility
            )

            if link.confidence >= 0.6:
                item.entity_link_confidence = link.confidence
                item.entity_link_signals = link.signals
                linked.append(item)

        # --- Risk aggregation ---
        weighted_score = calculate_weighted_score(linked)
        status = derive_risk_status(weighted_score)

        # --- LLM reasoning ---
        reason = self.reasoning.adverse_media_reason(
            name=name,
            articles=linked
        ) if linked else "No credible adverse media found."

        return AdverseMediaResult(
            query=name,
            total=len(linked),
            media=linked,
            weighted_score=weighted_score,
            reason=reason,
            status=status
        )
