# orchestrator.py
from typing import Optional
import logging

from services.audit_service import AuditService
from models.audit_models import AuditTrace

from schemas.pep_response import (
    ScreeningResponseSchema,
    PEPProfileSchema,
)

from services.news.provider_registry import ProviderRegistry
from services.news.providers.rss import RSSProvider
from services.news.providers.gnews import GNewsProvider
from services.news.providers.everypolitician import EveryPoliticianProvider
from services.news.providers.opensanctions import OpenSanctionsProvider

from config import settings
from utils.identity import normalize_name
from services.llm_service import LLMService

# ------------------------
# Logging setup
# ------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ScreeningOrchestrator:
    """
    Orchestrates identity → PEP → adverse media → audit
    Enforces strict DOMAIN → SCHEMA boundary at response time.
    """

    def __init__(self):
        from agents.pep_agent import PEPAgent
        from agents.adverse_media_agent import AdverseMediaAgent

        logger.info("Initializing ScreeningOrchestrator")

        # ---------- Provider Registry ----------
        registry = ProviderRegistry()

        if settings.RSS_FEEDS:
            registry.register(RSSProvider(settings.RSS_FEEDS))
            logger.info("RSSProvider registered (%d feeds)", len(settings.RSS_FEEDS))

        if settings.GNEWS_API_KEY:
            registry.register(GNewsProvider(settings.GNEWS_API_KEY))
            logger.info("GNewsProvider registered")

        registry.register(EveryPoliticianProvider())
        logger.info("EveryPoliticianProvider registered")

        if settings.OPENSANCTIONS_API_KEY:
            registry.register(
                OpenSanctionsProvider(api_key=settings.OPENSANCTIONS_API_KEY)
            )
            logger.info("OpenSanctionsProvider registered")

        # ---------- LLM Service ----------
        # Use Groq by default if key is present, else OpenAI
        if settings.GROQ_API_KEY:
            from groq import AsyncGroq
            llm_service = LLMService(
                client=AsyncGroq(api_key=settings.GROQ_API_KEY),
                model="moonshotai/kimi-k2-instruct-0905",
                temperature=0.0,
            )
            logger.info("LLM Service initialized with Groq")
        elif settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            llm_service = LLMService(
                client=AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
                model="gpt-4o-mini",
                temperature=0.0,
            )
            logger.info("LLM Service initialized with OpenAI")
        else:
            raise ValueError("No valid LLM API key found (GROQ_API_KEY or OPENAI_API_KEY)")

        # ---------- Agents ----------
        self.pep = PEPAgent(
            llm_service=llm_service,
            news_provider_registry=registry,
        )
        self.media = AdverseMediaAgent(registry, llm_service)
        self.audit = AuditService()

        logger.info("ScreeningOrchestrator initialization complete")

    # ------------------------------------------------------------------
    # Main entrypoint
    # ------------------------------------------------------------------
    async def run(
        self,
        query: str,
        country: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ScreeningResponseSchema:

        if not query or not query.strip():
            raise ValueError("Query name must be provided for screening")

        logger.info("Screening started for '%s' (%s)", query, country)

        trace = AuditTrace()

        # ---------- INPUT ----------
        trace.add_event(
            "INPUT_RECEIVED",
            {
                "query": query,
                "country": country,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        # ---------- IDENTITY ----------
        # replaced IdentityAgent.normalize_name with utility
        normalized_name_str = normalize_name(query)
        trace.add_event(
            "NAME_NORMALIZED",
            {"normalized_name": normalized_name_str},
        )

        # ---------- PEP (DOMAIN MODEL) ----------
        pep_profile = await self.pep.evaluate(normalized_name_str, country)
        trace.add_event(
            "PEP_EVALUATED",
            {
                "is_pep": pep_profile.is_pep,
                "pep_level": pep_profile.pep_level,
                "reason": pep_profile.reason,
            },
        )

        # ---------- ADVERSE MEDIA (DOMAIN MODEL) ----------
        media_result = await self.media.analyze(
            normalized_name_str,
            country=country,
            start_date=start_date,
            end_date=end_date,
        )
        trace.add_event(
            "ADVERSE_MEDIA_ANALYZED",
            {
                "total": media_result.total,
                "weighted_score": media_result.weighted_score,
                "status": media_result.status,
            },
        )

        # ---------- AUDIT ----------
        self.audit.persist(trace)

        logger.info(
            "Screening completed: is_pep=%s, pep_level=%s",
            pep_profile.is_pep,
            pep_profile.pep_level,
        )

        # ===========================
        # DOMAIN → SCHEMA CONVERSION 
        # ===========================

        pep_schema = PEPProfileSchema.model_validate(
            pep_profile.model_dump()
        )

        adverse_media_payload = media_result.model_dump()

        # ---------- RESPONSE ----------
        return ScreeningResponseSchema(
            pep=pep_schema,
            adverse_media=adverse_media_payload,
            audit_trace_id=trace.trace_id,
        )
