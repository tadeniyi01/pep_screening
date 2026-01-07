# agents/adverse_media_agent.py
import logging
from typing import Optional
from models.media_models import AdverseMediaResult
from services.evidence_service import EvidenceService
from services.news.provider_registry import ProviderRegistry
from utils.scoring import (
    suppress_false_positives,
    score_item,
    calculate_weighted_score,
    derive_risk_status,
)
from agents.sar_narrative_agent import SARNarrativeAgent
from agents.adverse_classifier_agent import AdverseClassifierAgent
from services.llm_service import LLMService

logger = logging.getLogger(__name__)
# ... (logging config)

class AdverseMediaAgent:
    def __init__(self, registry: ProviderRegistry, llm_service: LLMService):
        self.provider_registry = registry
        self.evidence = EvidenceService(registry)
        self.sar = SARNarrativeAgent()
        self.classifier = AdverseClassifierAgent(llm_service)

    async def analyze(
        self,
        name: str,
        country: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AdverseMediaResult:

        # ---------- FETCH ALL EVIDENCE ----------
        all_items = await self.evidence.fetch(
            query=name,
            country=country,
            start_date=start_date,
            end_date=end_date,
        )

        # ---------- AI CLASSIFICATION (PRECISION) ----------
        # Use LLM to classify items before scoring
        all_items = await self.classifier.classify(name, all_items)

        # ---------- SPLIT BY TYPE ----------
        adverse_media = [i for i in all_items if i.evidence_type == "adverse_media"]
        structured_pep = [i for i in all_items if i.evidence_type == "structured_pep"]

        # ---------- FALSE POSITIVE FILTER ----------
        adverse_media = suppress_false_positives(adverse_media, name)

        # ---------- SCORING ----------
        for item in adverse_media:
            item.final_score = score_item(item)

        # Structured PEP evidence never inflates score
        for item in structured_pep:
            item.final_score = 0.0
            item.explanation = (
                "Structured political exposure evidence used for corroboration only. "
                "Does not contribute to adverse media risk scoring."
            )

        combined = adverse_media + structured_pep

        # ---------- LOGGING ----------
        logger.info(
            "[AdverseMedia] %s: %d adverse media, %d structured PEP",
            name,
            len(adverse_media),
            len(structured_pep),
        )
        for item in adverse_media:
            logger.info(
                "[AdverseMedia] %s: '%s' (%s) -> score %.2f",
                name,
                getattr(item, "title", "No title"),
                getattr(item, "source", "Unknown"),
                getattr(item, "final_score", 0.0),
            )

        # ---------- AGGREGATION ----------
        weighted_score = calculate_weighted_score(adverse_media)
        status = derive_risk_status(weighted_score)

        # ---------- SAR NARRATIVE ----------
        sar_text = self.sar.generate(
            subject_name=name,
            articles=combined,
            overall_score=weighted_score,
            status=status,
        )

        # ---------- RETURN RESULT ----------
        reason_list = [
            f"{len(adverse_media)} adverse media articles identified.",
            f"{len(structured_pep)} structured PEP records identified.",
            f"Weighted adverse media score: {weighted_score}.",
            f"Overall risk classification: {status}.",
        ]

        # If no adverse media at all, mark status as 'Clear'
        if not adverse_media:
            weighted_score = 0.0
            status = "Clear"
            reason_list = [
                "No credible adverse media identified.",
                f"{len(structured_pep)} structured PEP references identified."
            ]
            logger.info("[AdverseMedia] No adverse media found. Status set to 'Clear'.")

        return AdverseMediaResult(
            query=name,
            total=len(combined),
            media=combined,
            weighted_score=weighted_score,
            status=status,
            reason=reason_list,
            sar_narrative=sar_text,
        )
