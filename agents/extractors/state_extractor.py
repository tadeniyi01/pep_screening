import re
from typing import Dict, List

from agents.confidence.attribute_confidence import score_attribute_confidence
from agents.extractors.ng_states import NIGERIAN_STATES


STATE_PATTERNS = [
    r"born in (?P<state>.+?) state",
    r"native of (?P<state>.+?) state",
    r"hails from (?P<state>.+?) state",
    r"state of origin[:\s]+(?P<state>.+?) state",
]


def extract_state_of_origin(
    subject_name: str,
    sources: List[dict],
    country: str | None = None
) -> Dict[str, float | str | None]:
    """
    Extract state of origin conservatively from text sources.
    """

    # Only Nigeria supported for now
    if country and country.upper() != "NG":
        return {
            "value": None,
            "confidence": 0.0
        }

    matches = []

    for src in sources:
        text = src.get("text", "").lower()
        source_type = src.get("source", "unknown")

        if not text:
            continue

        for pattern in STATE_PATTERNS:
            m = re.search(pattern, text)
            if not m:
                continue

            state = m.group("state").title()
            if state not in NIGERIAN_STATES:
                continue

            matches.append({
                "value": f"{state} State",
                "source": source_type
            })

    if not matches:
        return {
            "value": None,
            "confidence": 0.0
        }

    confidence = score_attribute_confidence(
        attribute="state",
        evidence=matches
    )

    return {
        "value": matches[0]["value"],
        "confidence": round(confidence, 2)
    }
