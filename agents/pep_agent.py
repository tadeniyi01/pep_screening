from datetime import datetime, timezone

from models.pep_models import (
    PEPProfile,
    ConfidenceValue,
    LifeStatus,
    AdditionalInformation
)

from agents.reasoning_agent import ReasoningAgent
from agents.disambiguation_agent import DisambiguationAgent
from agents.entity_linking_agent import EntityLinkingAgent
from services.pep_taxonomy_service import NigeriaPEPTaxonomyService
from agents.role_enrichment_agent import RoleEnrichmentAgent
from agents.role_enrichment.confidence_aggregator import RoleConfidenceAggregator
from services.llm_service import LLMService
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class PEPAgent:
    def __init__(self, llm_provider: str = "groq"):
        # --- Core agents ---
        self.reasoning = ReasoningAgent()
        self.disambiguator = DisambiguationAgent()
        self.entity_linker = EntityLinkingAgent()
        self.taxonomy = NigeriaPEPTaxonomyService()
        self.confidence_aggregator = RoleConfidenceAggregator()

        # --- LLM Provider Selection ---
        self.llm_service = self._init_llm(llm_provider)

        # --- Role enrichment ---
        self.role_enricher = RoleEnrichmentAgent(
            llm_service=self.llm_service
        )

    def _init_llm(self, provider: str) -> LLMService:
        """
        Centralized provider switching
        """

        if provider == "groq":
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            return LLMService(
                client=client,
                model="moonshotai/kimi-k2-instruct-0905",
                temperature=0.0
            )

        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key="OPENAI_KEY")
            return LLMService(
                client=client,
                model="gpt-4o-mini",
                temperature=0.0
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def evaluate(self, name: str, country: str) -> PEPProfile:
        candidate_name = name
        candidate_country = country

        # --- 0. ROLE DISCOVERY ---
        roles = self.role_enricher.enrich(name, country)
        print("DISCOVERED ROLES:", roles)

        if not roles:
            return self._not_pep(
                name,
                country,
                ["No public roles discovered"]
            )

        # --- 1. CONFIDENCE AGGREGATION ---
        aggregated_roles = self.confidence_aggregator.aggregate(roles)
        print("AGGREGATED ROLES:", aggregated_roles)

        trusted_roles = [
            r for r in aggregated_roles if r.confidence >= 0.75
        ]

        if not trusted_roles:
            return self._not_pep(
                name,
                country,
                ["No high-confidence public roles found"]
            )

        # --- 2. CURRENT VS PREVIOUS POSITIONS ---
        current_year = datetime.now(timezone.utc).year

        current_positions = []
        previous_positions = []

        for role in trusted_roles:
            if role.end_year is None or role.end_year >= current_year:
                current_positions.append(role.title)
            else:
                previous_positions.append(role.title)

        primary_role = next(
            (r for r in trusted_roles if r.end_year is None),
            trusted_roles[0]
        )

        candidate_positions = current_positions
        candidate_org = primary_role.organisation

        # --- 3. DISAMBIGUATION ---
        disamb = self.disambiguator.disambiguate(
            query_name=name,
            candidate_name=candidate_name,
            candidate_country=candidate_country,
            query_country=country
        )

        if not disamb["match"]:
            return self._not_pep(
                name,
                country,
                ["Name disambiguation failed"]
            )

        # --- 4. ENTITY LINKING ---
        link = self.entity_linker.link(
            query_name=name,
            candidate_name=candidate_name,
            query_country=country,
            candidate_country=candidate_country,
            query_positions=candidate_positions,
            candidate_positions=candidate_positions,
            query_org=candidate_org,
            candidate_org=candidate_org,
            source_credibility=1.0
        )

        if link.confidence < 0.65:
            return self._not_pep(
                name,
                country,
                ["Low entity linking confidence"]
            )

        # --- 5. TAXONOMY CLASSIFICATION ---
        taxonomy = self.taxonomy.classify(candidate_positions)

        if taxonomy["pep_level"] == "Not a PEP":
            return self._not_pep(
                name,
                country,
                ["No Nigeria PEP role matched"]
            )

        # --- 6. REASONING ---
        reasons = self.reasoning.pep_reason(
            name=name,
            positions=candidate_positions,
            level=taxonomy["pep_level"]
        )

        reasons.extend(disamb["reasons"])
        reasons.extend(link.signals)
        reasons.append(
            f"Matched Nigeria PEP role: {taxonomy['matched_role']}"
        )

        # --- 7. FINAL PROFILE ---
        return PEPProfile(
            name=name,
            gender=ConfidenceValue(
                value="Male",
                confidence="High"
            ),
            middle_name="",
            aliases=[],
            other_names=[],
            is_pep=True,
            pep_level=taxonomy["pep_level"],
            organisation_or_party=candidate_org,
            current_positions=current_positions,
            previous_positions=previous_positions,
            date_of_birth="",
            age=None,
            education=[],
            relatives=[],
            associates=[],
            state="",
            country=country,
            reason=reasons,
            alive_or_deceased=LifeStatus(
                status="Alive",
                date_of_death=""
            ),
            pep_association=False,
            basis_for_pep_association="",
            links=[],
            information_recency="",
            image=[],
            additional_information=AdditionalInformation(),
            titles=candidate_positions
        )

    # --- Helper ---
    def _not_pep(self, name, country, reasons):
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
            reason=reasons,
            alive_or_deceased=None,
            pep_association=False,
            basis_for_pep_association="",
            links=[],
            information_recency="",
            image=[],
            additional_information=AdditionalInformation(),
            titles=[]
        )
