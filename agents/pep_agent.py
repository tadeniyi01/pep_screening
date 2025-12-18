# agents/pep_agent.py
from datetime import datetime, timezone
import os
import re
from dotenv import load_dotenv
from typing import List

from models.pep_models import (
    PEPProfile,
    ConfidenceValue,
    LifeStatus,
    AdditionalInformation
)

from agents.reasoning_agent import ReasoningAgent
from agents.disambiguation_agent import DisambiguationAgent
from agents.entity_linking_agent import EntityLinkingAgent
from agents.role_enrichment_agent import RoleEnrichmentAgent
from agents.role_enrichment.confidence_aggregator import RoleConfidenceAggregator
from agents.reason_summarization_agent import ReasonSummarizationAgent
from agents.social_profile_agent import SocialProfileAgent
from agents.biographic_enrichment_agent import BiographicEnrichmentAgent

from services.pep_taxonomy_service import NigeriaPEPTaxonomyService
from services.llm_service import LLMService

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _number_reason_paragraphs(paragraphs: list[str]) -> list[str]:
    numbered = []

    for i, p in enumerate(paragraphs, start=1):
        if p.strip().startswith("[") and p.strip().endswith("]"):
            raise ValueError(
                "Received stringified list instead of List[str] in reasons"
            )

        numbered.append(f"{i}. {p.strip()}")

    return numbered



class PEPAgent:
    def __init__(self, llm_provider: str = "groq"):
        # --- Core agents ---
        self.reasoning = ReasoningAgent()
        self.disambiguator = DisambiguationAgent()
        self.entity_linker = EntityLinkingAgent()
        self.taxonomy = NigeriaPEPTaxonomyService()
        self.confidence_aggregator = RoleConfidenceAggregator()
        self.biographic_enricher = BiographicEnrichmentAgent()

        # --- LLM ---
        self.llm_service = self._init_llm(llm_provider)
        self.reason_summarizer = ReasonSummarizationAgent(self.llm_service)
        self.social_profile_agent = SocialProfileAgent(self.llm_service)

        # --- Role enrichment ---
        self.role_enricher = RoleEnrichmentAgent(llm_service=self.llm_service)

    def _init_llm(self, provider: str) -> LLMService:
        if provider == "groq":
            from groq import Groq
            return LLMService(
                client=Groq(api_key=GROQ_API_KEY),
                model="moonshotai/kimi-k2-instruct-0905",
                temperature=0.0
            )

        if provider == "openai":
            from openai import OpenAI
            return LLMService(
                client=OpenAI(api_key=OPENAI_API_KEY),
                model="gpt-4o-mini",
                temperature=0.0
            )

        raise ValueError(f"Unsupported LLM provider: {provider}")

    def evaluate(self, name: str, country: str) -> PEPProfile:
        candidate_name = name
        candidate_country = country

        # --- 0. ROLE DISCOVERY ---
        roles = self.role_enricher.enrich(name, country)
        print("DISCOVERED ROLES:", roles)

        if not roles:
            return self._not_pep(name, country, ["1. No public roles discovered."])

        # --- 1. CONFIDENCE AGGREGATION ---
        aggregated_roles = self.confidence_aggregator.aggregate(roles)
        print("AGGREGATED ROLES:", aggregated_roles)

        trusted_roles = [r for r in aggregated_roles if r.confidence >= 0.75]

        if not trusted_roles:
            return self._not_pep(
                name, country, ["1. Public roles identified but none met confidence threshold."]
            )

        # --- 2. CURRENT / PREVIOUS POSITIONS ---
        current_year = datetime.now(timezone.utc).year
        current_positions, previous_positions = [], []

        for role in trusted_roles:
            if role.end_year is None or role.end_year >= current_year:
                current_positions.append(role.title)
            else:
                previous_positions.append(role.title)

        primary_role = next((r for r in trusted_roles if r.end_year is None), trusted_roles[0])
        candidate_org = primary_role.organisation

        # --- 3. DISAMBIGUATION ---
        disamb = self.disambiguator.disambiguate(
            query_name=name,
            candidate_name=candidate_name,
            candidate_country=candidate_country,
            query_country=country
        )
        if not disamb.get("match"):
            return self._not_pep(name, country, ["1. Name disambiguation failed — identity could not be confirmed."])

        # --- 4. ENTITY LINKING ---
        link = self.entity_linker.link(
            query_name=name,
            candidate_name=candidate_name,
            query_country=country,
            candidate_country=candidate_country,
            query_positions=current_positions,
            candidate_positions=current_positions,
            query_org=candidate_org,
            candidate_org=candidate_org,
            source_credibility=1.0
        )
        if link.confidence < 0.65:
            return self._not_pep(name, country, ["1. Entity linking confidence below acceptable threshold."])

        # --- 5. TAXONOMY ---
        taxonomy = self.taxonomy.classify(current_positions)
        if taxonomy["pep_level"] == "Not a PEP":
            return self._not_pep(name, country, ["1. No Nigeria PEP role matched taxonomy criteria."])

        # --- 6. BIOGRAPHIC ENRICHMENT ---
        # Pass evidence sources into biographic enricher: role sources often include raw_reference/text
        # RoleEnrichmentAgent should already return roles with raw_reference and possibly a 'evidence' list.
        # We'll construct a conservative 'sources' list for biographic extraction:
        sources_for_bio = []
        for r in aggregated_roles:
            src = {"source": r.source, "text": getattr(r, "raw_text", "") or "", "image_url": getattr(r, "image_url", None)}
            # if raw_reference is a URL string, include it so image/links detection can pick it up
            if getattr(r, "raw_reference", None):
                src.setdefault("url", r.raw_reference)
            sources_for_bio.append(src)

        # also include entity_link signals if available
        if getattr(link, "signals", None):
            for s in link.signals:
                sources_for_bio.append({"source": "entity_link", "text": str(s)})

        bio = self.biographic_enricher.enrich(
            name=name,
            country=country,
            sources=sources_for_bio,
            roles=trusted_roles
        )

        # --- 7. LINKS & IMAGE AGGREGATION ---
        link_set = set()
        # aggregated_roles raw_reference (if string)
        for r in aggregated_roles:
            rr = getattr(r, "raw_reference", None)
            if rr:
                # raw_reference might be JSON; try to include if it's a URL-like string
                if isinstance(rr, str) and (rr.startswith("http") or "://" in rr):
                    link_set.add(rr)
                else:
                    # keep non-URL raw_reference too for audit (but not in links to UI)
                    pass

        # include social profile urls if present in social resolve
        social = self.social_profile_agent.resolve(name=name, country=country)
        for k in ["linkedin_profile", "twitter_profile", "facebook_profile", "instagram_profile"]:
            p = social.get(k) or {}
            url = p.get("url") or p.get("profile_url")
            if url:
                link_set.add(url)

        # include images from bio
        images = bio.get("image", []) or []
        for img in images:
            if isinstance(img, dict):
                url = img.get("url")
            else:
                url = img
            if url:
                link_set.add(url)

        links = sorted(link_set)

        # --- 8. INFORMATION RECENCY ---
        years = [r.start_year for r in trusted_roles if r.start_year]
        information_recency = f"Verified as of {max(years)}" if years else "Recency undetermined"

        # --- 9. REASON SUMMARIZATION via LLM ---
        reason_payload = {
            "entity": {"name": name, "country": country},
            "accepted_roles": [
                {
                    "title": r.title,
                    "organisation": r.organisation,
                    "source": r.source,
                    "confidence": r.confidence,
                    "status": "current" if r.end_year is None else "previous"
                }
                for r in trusted_roles
            ],
            "rejected_roles": [
                {
                    "title": r.title,
                    "organisation": r.organisation,
                    "source": r.source,
                    "confidence": r.confidence,
                    "reason": "Below confidence threshold"
                }
                for r in aggregated_roles if r.confidence < 0.75
            ],
            "disambiguation": disamb,
            "entity_linking_confidence": getattr(link, "confidence", None),
            "taxonomy": taxonomy,
            "links": links
        }

        final_reason_list = self.reason_summarizer.summarize(reason_payload) or []
        
        numbered_reason_list = _number_reason_paragraphs(final_reason_list)

        # if the summarizer returned no distinct paragraphs, fall back to deterministic basis
        if not numbered_reason_list:
            basis = [r.title for r in trusted_roles]
            numbered_reason_list = [
                f"1. Deterministic basis: roles confirmed: {', '.join(basis)}"
            ]

        # --- 10. basis_for_pep_association (deterministic short string) ---
        basis_for_pep_association = "; ".join(
            [f"{r.title} ({r.source}, conf={r.confidence})" for r in trusted_roles]
        )

        # --- 11. FINAL PROFILE POPULATION: pull biographic fields safely ---
        return PEPProfile(
            name=name,
            gender=ConfidenceValue(value=bio.get("gender") or "Male", confidence="High") if bio.get("gender") else ConfidenceValue(value="Male", confidence="High"),
            middle_name=bio.get("middle_name", "") or "",
            aliases=bio.get("aliases", []),
            other_names=bio.get("other_names", []),
            is_pep=True,
            pep_level=taxonomy.get("pep_level", "Unknown"),
            organisation_or_party=candidate_org,
            current_positions=current_positions,
            previous_positions=previous_positions,
            date_of_birth=bio.get("date_of_birth", "") or "",
            age=bio.get("age"),
            education=bio.get("education", []),
            relatives=bio.get("relatives", []),
            associates=bio.get("associates", []),
            state=bio.get("state", "") or "",
            country=country,
            reason=numbered_reason_list,
            alive_or_deceased=LifeStatus(status=bio.get("alive_or_deceased", "Alive"), date_of_death=""),
            pep_association=False,
            basis_for_pep_association=basis_for_pep_association,
            links=links,
            information_recency=information_recency,
            image=[img if isinstance(img, str) else img.get("url") for img in images],
            additional_information=AdditionalInformation(
                linkedin_profile=social.get("linkedin_profile", {}),
                instagram_profile=social.get("instagram_profile", {}),
                facebook_profile=social.get("facebook_profile", {}),
                twitter_profile=social.get("twitter_profile", {}),
                notable_achievements=bio.get("notable_achievements", [])
            ),
            titles=current_positions
        )

    # --- Helper for not-PEP responses ---
    def _not_pep(self, name, country, reasons: List[str]):
        # ensure reasons is a list of properly numbered strings
        numbered = []
        for i, r in enumerate(reasons):
            # if already a numbered string, keep; otherwise add numbering
            if re.match(r"^\s*\d+\.", r):
                numbered.append(r.strip())
            else:
                numbered.append(f"{i+1}. {r.strip()}")
        return PEPProfile(
            name=name,
            gender=None,
            middle_name="",
            aliases=[],
            other_names=[],
            is_pep=False,
            pep_level="Not a PEP",
            organisation_or_party="",
            current_positions=[],
            previous_positions=[],
            date_of_birth="",
            age=None,
            education=[],
            relatives=[],
            associates=[],
            state="",
            country=country,
            reason=numbered,
            alive_or_deceased=None,
            pep_association=False,
            basis_for_pep_association="",
            links=[],
            information_recency="",
            image=[],
            additional_information=AdditionalInformation(),
            titles=[]
        )
