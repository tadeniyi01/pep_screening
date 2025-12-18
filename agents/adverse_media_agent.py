from typing import Optional
from models.media_models import AdverseMediaResult
from services.news_service import NewsService
from services.news.provider_registry import ProviderRegistry
from utils.scoring import (
    suppress_false_positives,
    score_item,
    calculate_weighted_score,
    derive_risk_status,
)
from agents.sar_narrative_agent import SARNarrativeAgent


class AdverseMediaAgent:
    def __init__(self, registry: ProviderRegistry):
        self.news = NewsService(registry)
        self.sar = SARNarrativeAgent()

    def analyze(
        self,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AdverseMediaResult:

        # ---------- Fetch ----------
        raw_articles = self.news.fetch(
            query=name,
            start_date=start_date,
            end_date=end_date
        )

        # ---------- Filter ----------
        filtered = suppress_false_positives(raw_articles, name)

        for item in filtered:
            item.final_score = score_item(item)

        if not filtered:
            sar_text = self.sar.generate(
                subject_name=name,
                articles=[],
                overall_score=0.0,
                status="Clear",
            )

            return AdverseMediaResult(
                query=name,
                total=0,
                media=[],
                weighted_score=0.0,
                status="Clear",
                reason=["No credible adverse media identified."],
                sar_narrative=sar_text,
            )

        # ---------- Aggregate ----------
        weighted_score = calculate_weighted_score(filtered)
        status = derive_risk_status(weighted_score)

        sar_text = self.sar.generate(
            subject_name=name,
            articles=filtered,
            overall_score=weighted_score,
            status=status,
        )

        return AdverseMediaResult(
            query=name,
            total=len(filtered),
            media=filtered,
            weighted_score=weighted_score,
            status=status,
            reason=[
                f"{len(filtered)} adverse media articles identified.",
                f"Weighted adverse media score: {weighted_score}.",
                f"Overall risk classification: {status}.",
            ],
            sar_narrative=sar_text,
        )
