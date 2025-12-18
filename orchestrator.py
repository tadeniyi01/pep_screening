from typing import Optional

from services.audit_service import AuditService
from models.audit_models import AuditTrace
from schemas.pep_response import ScreeningResponseSchema

from services.news.provider_registry import ProviderRegistry
from services.news.providers.rss import RSSProvider
from services.news.providers.gnews import GNewsProvider

from config import settings


class ScreeningOrchestrator:
    def __init__(self):
        from agents.identity_agent import IdentityAgent
        from agents.pep_agent import PEPAgent
        from agents.adverse_media_agent import AdverseMediaAgent

        # ---------- Provider Registry ----------
        registry = ProviderRegistry()

        # RSS is safe (no API key required)
        if settings.RSS_FEEDS:
            registry.register(RSSProvider(settings.RSS_FEEDS))

        # GNews is optional (API-key guarded)
        if settings.GNEWS_API_KEY:
            registry.register(GNewsProvider(settings.GNEWS_API_KEY))

        # ---------- Agents ----------
        self.identity = IdentityAgent()
        self.pep = PEPAgent()
        self.media = AdverseMediaAgent(registry)
        self.audit = AuditService()

    def run(
        self,
        query: str,
        country: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ScreeningResponseSchema:

        if not query or not query.strip():
            raise ValueError("Query name must be provided for screening")

        trace = AuditTrace()

        # ---------- INPUT ----------
        trace.add_event(
            "INPUT_RECEIVED",
            {
                "query": query,
                "country": country,
                "start_date": start_date,
                "end_date": end_date,
            }
        )

        # ---------- IDENTITY ----------
        normalized_name = self.identity.normalize_name(query)
        trace.add_event(
            "NAME_NORMALIZED",
            {"normalized_name": normalized_name}
        )

        # ---------- PEP ----------
        pep_profile = self.pep.evaluate(normalized_name, country)
        trace.add_event(
            "PEP_EVALUATED",
            {
                "is_pep": pep_profile.is_pep,
                "pep_level": pep_profile.pep_level,
                "reason": pep_profile.reason,
            }
        )

        # ---------- ADVERSE MEDIA ----------
        media_result = self.media.analyze(
            normalized_name,
            start_date=start_date,
            end_date=end_date,
        )
        trace.add_event(
            "ADVERSE_MEDIA_ANALYZED",
            {
                "total": media_result.total,
                "weighted_score": media_result.weighted_score,
                "status": media_result.status,
            }
        )

        # ---------- AUDIT ----------
        self.audit.persist(trace)

        # ---------- RESPONSE ----------
        return ScreeningResponseSchema(
           pep=pep_profile.model_dump(),
           adverse_media=media_result.model_dump(),
           audit_trace_id=trace.trace_id,
)       