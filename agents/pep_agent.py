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


class PEPAgent:
    def __init__(self):
        self.reasoning = ReasoningAgent()
        self.disambiguator = DisambiguationAgent()
        self.entity_linker = EntityLinkingAgent()
        self.taxonomy = NigeriaPEPTaxonomyService()

    def evaluate(self, name: str, country: str) -> PEPProfile:
        candidate_name = name
        candidate_country = country
        candidate_positions = ["President"]
        candidate_org = "Goverment of the Federal Republic of Nigeria"

        # --- 1. DISAMBIGUATION ---
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

        # --- 2. ENTITY LINKING ---
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

        # --- 3. TAXONOMY ---
        taxonomy = self.taxonomy.classify(candidate_positions)

        if taxonomy["pep_level"] == "Not a PEP":
            return self._not_pep(
                name,
                country,
                ["No Nigeria PEP role matched"]
            )

        # --- 4. REASONING ---
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

        # --- 5. FINAL PROFILE ---
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
            current_positions=candidate_positions,
            previous_positions=[],
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
            titles=[]
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
