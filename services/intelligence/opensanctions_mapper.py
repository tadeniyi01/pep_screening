# services/intelligence/opensanctions_mapper.py

from typing import List
from models.evidence_models import Evidence
from models.opensanctions_models import OpenSanctionsEntity
from utils.source_weights import SOURCE_WEIGHTS

def map_opensanctions_to_evidence(
    entities: List[OpenSanctionsEntity]
) -> List[Evidence]:

    evidences: List[Evidence] = []

    for entity in entities:
        base_confidence = min(entity.score, 1.0)

        # --- PEP / Political Roles ---
        for position in entity.positions:
            evidences.append(
                Evidence(
                    source="opensanctions",
                    source_weight=SOURCE_WEIGHTS["opensanctions"],
                    claim_type="PEP_ROLE",
                    claim_value=position.title,
                    start_date=position.start_date,
                    end_date=position.end_date,
                    confidence=round(
                        SOURCE_WEIGHTS["opensanctions"] * base_confidence, 2
                    ),
                    raw_reference=f"https://opensanctions.org/entities/{entity.entity_id}",
                )
            )

        # --- Sanctions / Risk Topics ---
        for topic in entity.topics:
            evidences.append(
                Evidence(
                    source="opensanctions",
                    source_weight=SOURCE_WEIGHTS["opensanctions"],
                    claim_type="RISK_TOPIC",
                    claim_value=topic,
                    start_date=None,
                    end_date=None,
                    confidence=round(
                        SOURCE_WEIGHTS["opensanctions"] * base_confidence, 2
                    ),
                    raw_reference=f"https://opensanctions.org/entities/{entity.entity_id}",
                )
            )

    return evidences
