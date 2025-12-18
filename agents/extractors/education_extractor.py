import re
from typing import List, Dict

from agents.confidence.attribute_confidence import score_attribute_confidence


DEGREE_PATTERNS = [
    r"\b(BSc|BA|LLB|MBA|MSc|PhD|Doctorate)\b",
    r"\b(Bachelor|Master|Doctor)\s+of\b"
]


def extract_education(
    subject_name: str,
    sources: List[Dict]
) -> Dict[str, List[Dict] | float]:
    """
    Extract education-related information conservatively from sources.
    """

    education: List[Dict] = []
    evidence: List[Dict] = []

    for src in sources:
        text = src.get("text", "")
        source_type = src.get("source", "unknown")

        if not text:
            continue

        if not any(re.search(p, text, re.IGNORECASE) for p in DEGREE_PATTERNS):
            continue

        education.append({
            "description": text.strip()[:250],
            "source": source_type
        })

        evidence.append({
            "value": text.strip(),
            "source": source_type
        })

    if not education:
        return {
            "value": [],
            "confidence": 0.0
        }

    confidence = score_attribute_confidence(
        attribute="education",
        evidence=evidence
    )

    return {
        "value": education,
        "confidence": round(confidence, 2)
    }
