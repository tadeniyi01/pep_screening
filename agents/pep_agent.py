# agents/pep_agent.py

from datetime import datetime, date, timezone
import os
from typing import List, Optional
import logging

from config import settings

# =========================
# Models (DOMAIN)
# =========================
from models.pep_models import (
    PEPProfile,
    ConfidenceValue,
    LifeStatus,
    AdditionalInformation,
)

# NOTE: Kept for compatibility / schema boundary
from schemas.pep_response import (
    PEPProfileSchema,
    AdditionalInformationSchema,
    ConfidenceValueSchema,
    LifeStatusSchema,
)

# =========================
# Agents
# =========================
from agents.role_discovery.wikidata_role_source import WikidataRoleSource
from agents.reasoning_agent import ReasoningAgent, normalize_reason_output
from agents.disambiguation_agent import DisambiguationAgent
from agents.entity_linking_agent import EntityLinkingAgent
from agents.role_enrichment_agent import RoleEnrichmentAgent
from agents.role_enrichment.confidence_aggregator import RoleConfidenceAggregator
from agents.reason_summarization_agent import ReasonSummarizationAgent
from agents.social_profile_agent import SocialProfileAgent
from agents.biographic_enrichment_agent import BiographicEnrichmentAgent

# =========================
# Services
# =========================
from services.pep_taxonomy_service import NigeriaPEPTaxonomyService
from services.llm_service import LLMService

# =========================
# Utils
# =========================
from utils.role_resolution import split_current_previous_roles
from utils.reason_paragraphs import _number_reason_paragraphs
from utils.llm_bio_helper import (
    _infer_gender,
    _infer_aliases,
    _infer_alive_or_deceased,
    _infer_associates,
    _infer_state,
    _infer_dob,
    _infer_education,
    _infer_relatives,
    _infer_notable_achievements,
)

# =========================
# Logging
# =========================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(handler)


# ============================================================
# PEP Agent
# ============================================================
class PEPAgent:
    """
    Evidence-first PEP determination agent.
    Structured sources are authoritative; LLM is assistive.
    """

    CURRENT_YEAR = datetime.now(timezone.utc).year

    def __init__(self, llm_service: LLMService, news_provider_registry=None):
        # Injected dependency
        self.llm_service = llm_service
        
        self.reasoning = ReasoningAgent(self.llm_service)
        self.disambiguator = DisambiguationAgent()
        self.entity_linker = EntityLinkingAgent()
        self.confidence_aggregator = RoleConfidenceAggregator()
        self.biographic_enricher = BiographicEnrichmentAgent()
        self.wikidata_role_source = WikidataRoleSource()
        self.taxonomy = NigeriaPEPTaxonomyService()

        # Injected dependency
        self.llm_service = llm_service
        
        self.reason_summarizer = ReasonSummarizationAgent(self.llm_service)
        self.social_profile_agent = SocialProfileAgent(self.llm_service)

        self.role_enricher = RoleEnrichmentAgent(
            news_provider_registry=news_provider_registry
        )

        logger.info("PEPAgent initialized with injected LLM service")

    # ------------------------------------------------------------
    # Structured Evidence Gate
    # ------------------------------------------------------------
    def _evaluate_structured_pep(
        self, evidence: Optional[List[dict]]
    ) -> tuple[bool, List[str], List[str]]:

        if not evidence:
            return False, [], []

        confirmed_roles: List[str] = []
        reasons: List[str] = []

        for e in evidence:
            if e.get("type") != "structured_pep":
                continue

            confidence = e.get("confidence", 0.0)
            if confidence < 0.80:
                continue

            role = e.get("role", "Public Office Holder")
            org = e.get("organisation", "")
            source = e.get("source", "Unknown")

            confirmed_roles.append(role)
            reasons.append(
                f"{source} confirms public office role: {role}"
                f"{' at ' + org if org else ''} (confidence {confidence})."
            )

        if confirmed_roles:
            return True, confirmed_roles, _number_reason_paragraphs(reasons)

        return False, [], []

    def _build_structured_pep_profile(
        self,
        name: str,
        country: str,
        roles: List[str],
        numbered_reasons: List[str],
    ) -> PEPProfile:

        return PEPProfile(
            name=name,
            gender=None,
            middle_name="",
            aliases=[],
            other_names=[],
            is_pep=True,
            pep_level="PEP",
            organisation_or_party="",
            current_positions=roles,
            previous_positions=[],
            date_of_birth="",
            age=None,
            education=[],
            relatives=[],
            associates=[],
            state="",
            country=country,
            reason=numbered_reasons,
            alive_or_deceased=None,
            pep_association=False,
            basis_for_pep_association="; ".join(roles),
            links=[],
            information_recency="Verified via structured open-source datasets",
            image=[],
            additional_information=AdditionalInformation(),
            titles=roles,
        )

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    @staticmethod
    def calculate_age(dob: str) -> ConfidenceValue:
        try:
            birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
            return ConfidenceValue(value=str(age), confidence="High")
        except Exception:
            return ConfidenceValue(value="Unknown", confidence="Low")

    def _roles_imply_alive(self, roles) -> bool:
        for role in roles:
            # Must be explicitly marked current
            if getattr(role, "is_current", False) is True:
                return True

            # End date must be both present AND recent
            end_date = getattr(role, "end_date", None)
            if end_date:
                try:
                    if end_date.year >= self.CURRENT_YEAR - 1:
                        return True
                except Exception:
                    pass

        return False


    async def _resolve_life_status(self, name: str, bio: dict, roles) -> LifeStatus:
        # 1. Explicit death date
        if bio.get("date_of_death"):
            return LifeStatus(
                status="Deceased",
                date_of_death=bio.get("date_of_death") or None
            )
    
        # 2. DOB sanity check
        dob = bio.get("date_of_birth")
        if dob:
            age_cv = self.calculate_age(dob)
            try:
                if int(age_cv.value) > 120:
                    return LifeStatus(status="Deceased", date_of_death="")
            except Exception:
                pass
            
        # 3. LLM fallback
        inferred = await _infer_alive_or_deceased(name, self.llm_service)
        inferred_status = None
        inferred_date_of_death = None
    
        if isinstance(inferred, LifeStatus):
            inferred_status = inferred.status
            inferred_date_of_death = inferred.date_of_death
        elif hasattr(inferred, "status"):
            inferred_status = inferred.status
            inferred_date_of_death = getattr(inferred, "date_of_death", None)
        elif isinstance(inferred, str) and inferred in {"Alive", "Deceased"}:
            inferred_status = inferred
    
        # 4. Role-based weak signal (ONLY if LLM inconclusive)
        if inferred_status is None or inferred_status == "Unknown":
            if roles and self._roles_imply_alive(roles):
                return LifeStatus(status="Alive", date_of_death="")
    
        # 5. Return what LLM inferred if available
        if inferred_status in {"Alive", "Deceased"}:
            return LifeStatus(status=inferred_status, date_of_death=inferred_date_of_death)
    
        # 6. Safe default
        return LifeStatus(status="Unknown", date_of_death="")


    # ------------------------------------------------------------
    # Main Evaluation
    # ------------------------------------------------------------
    async def evaluate(
        self,
        name: str,
        country: str,
        structured_evidence: Optional[List[dict]] = None,
    ) -> PEPProfile:
        try:
            # ---------- Structured evidence ----------
            is_structured, roles, reasons = self._evaluate_structured_pep(
                structured_evidence
            )
            if is_structured:
                return self._build_structured_pep_profile(
                    name, country, roles, reasons
                )

            # ---------- Role enrichment ----------
            enriched = await self.role_enricher.enrich(name, country)
            roles = enriched.get("roles", [])
            bio = enriched.get("evidence", {})

            if not roles:
                return self._not_pep(name, country, ["No public roles discovered."])

            aggregated = self.confidence_aggregator.aggregate(roles)
            trusted = [r for r in aggregated if r.confidence >= 0.75]

            if not trusted:
                return self._not_pep(
                    name, country, ["No roles met confidence threshold."]
                )

            current, previous = split_current_previous_roles(
                trusted, self.taxonomy
            )
            primary = max(trusted, key=lambda r: r.confidence)

            # ---------- Disambiguation ----------
            if not self.disambiguator.disambiguate(
                query_name=name,
                candidate_name=name,
                query_country=country,
                candidate_country=country,
            ).get("match"):
                return self._not_pep(name, country, ["Name disambiguation failed."])

            # ---------- Entity linking ----------
            link = self.entity_linker.link(
                query_name=name,
                candidate_name=name,
                query_country=country,
                candidate_country=country,
                query_positions=current,
                candidate_positions=current,
                query_org=primary.organisation,
                candidate_org=primary.organisation,
                source_credibility=1.0,
            )

            if link.confidence < 0.65:
                return self._not_pep(
                    name, country, ["Entity linking confidence too low."]
                )

            taxonomy = self.taxonomy.classify(current)
            if taxonomy.get("pep_level") == "Not a PEP":
                return self._not_pep(
                    name, country, ["Roles do not meet PEP taxonomy criteria."]
                )

            # ---------- Reasons ----------
            raw = await self.reason_summarizer.summarize(
                {
                    "entity": {"name": name, "country": country},
                    "roles": [
                        {
                            "title": r.title,
                            "organisation": r.organisation,
                            "confidence": r.confidence,
                        }
                        for r in trusted
                    ],
                    "taxonomy": taxonomy,
                    "entity_linking_confidence": link.confidence,
                }
            )

            numbered = _number_reason_paragraphs(normalize_reason_output(raw))

            # ---------- Bio ----------
            dob = bio.get("date_of_birth") or await _infer_dob(name, self.llm_service)
            age = self.calculate_age(dob) if dob else ConfidenceValue(value="Unknown", confidence="Low")

            # ---------- Gender ----------
            gender = None
            if isinstance(bio.get("gender"), str):
                gender = ConfidenceValue(value=bio["gender"], confidence="High")
            else:
                inferred = await _infer_gender(name, self.llm_service)
                if isinstance(inferred, str):
                    gender = ConfidenceValue(value=inferred, confidence="Low")
                elif hasattr(inferred, "value"):
                    gender = ConfidenceValue(
                        value=inferred.value,
                        confidence=inferred.confidence or "Low",
                    )
                else:
                    gender = ConfidenceValue(value="Unknown", confidence="Low")

            # ---------- Life status ----------
            alive_or_deceased = await self._resolve_life_status(name, bio, trusted)

            # ---------- Social profiles ----------
            social = await self.social_profile_agent.resolve(name=name, country=country)
            linkedin = social.get("linkedin") or social.get("linkedin_profile") or {}
            twitter = social.get("twitter") or social.get("twitter_profile") or {}
            facebook = social.get("facebook") or social.get("facebook_profile") or {}
            instagram = (
                social.get("instagram") or social.get("instagram_profile") or {}
            )

            # ---------- Final profile ----------
            return PEPProfile(
                name=name,
                gender=gender,
                middle_name=bio.get("middle_name", ""),
                aliases=await _infer_aliases(name, self.llm_service),
                other_names=bio.get("other_names", []),
                is_pep=True,
                pep_level=taxonomy.get("pep_level", "PEP"),
                organisation_or_party=primary.organisation or "",
                current_positions=current,
                previous_positions=previous,
                date_of_birth=dob or "",
                age=age,
                education=await _infer_education(name, self.llm_service),
                relatives=await _infer_relatives(name, self.llm_service),
                associates=await _infer_associates(name, self.llm_service),
                state=await _infer_state(name, self.llm_service),
                country=country,
                reason=numbered,
                alive_or_deceased=alive_or_deceased,
                pep_association=False,
                basis_for_pep_association="; ".join(numbered),
                links=[],
                information_recency=f"Verified as of {datetime.utcnow().year}",
                image=bio.get("images", []),
                additional_information=AdditionalInformation(
                    linkedin_profile=linkedin,
                    twitter_profile=twitter,
                    facebook_profile=facebook,
                    instagram_profile=instagram,
                    notable_achievements=bio.get("notable_achievements", []),
                ),
                titles=current,
            )

        except Exception as e:
            logger.exception("Unexpected error evaluating PEP")
            return self._not_pep(name, country, [f"Internal error: {e}"])

    # ------------------------------------------------------------
    # Not PEP
    # ------------------------------------------------------------
    def _not_pep(self, name: str, country: str, reasons: List[str]) -> PEPProfile:
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
            reason=_number_reason_paragraphs(reasons),
            alive_or_deceased=None,
            pep_association=False,
            basis_for_pep_association="",
            links=[],
            information_recency="Verification date unknown",
            image=[],
            additional_information=AdditionalInformation(),
            titles=[],
        )
