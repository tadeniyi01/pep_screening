# agents/extractors/associates_extractor.py

from typing import List, Dict
import re

from agents.confidence.attribute_confidence import score_attribute_confidence


ASSOCIATE_KEYWORDS = [
    "close associate",
    "political ally",
    "longtime ally",
    "chief of staff",
    "advisor to",
    "aide to",
    "business partner",
    "associate of",
    "protégé",
]


ALLOWED_SOURCES = {
    "news",
    "official_registry",
    "wikidata"
}


def extract_associates(
    subject_name: str,
    sources: List[Dict]
) -> Dict[str, object]:
    """
    Extract explicitly mentioned associates only.
    No inference, no escalation.
    Returns normalized { value, confidence }.
    """

    associates: List[Dict[str, str]] = []
    evidence: List[Dict[str, str]] = []

    for source in sources:
        text = source.get("text") or source.get("summary", "")
        source_type = source.get("source", "unknown")

        if not text or source_type not in ALLOWED_SOURCES:
            continue

        lower = text.lower()
        if subject_name.lower() not in lower:
            continue

        for keyword in ASSOCIATE_KEYWORDS:
            if keyword not in lower:
                continue

            # Conservative name capture (explicit nearby names only)
            matches = re.findall(
                r"(?:of|to)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)",
                text
            )

            for name in matches:
                clean_name = name.strip()

                # Prevent self-reference
                if clean_name.lower() == subject_name.lower():
                    continue

                associates.append({
                    "name": clean_name,
                    "relationship": keyword,
                    "source": source_type
                })

                evidence.append({
                    "value": f"{keyword}:{clean_name}",
                    "source": source_type
                })

    if not associates:
        return {
            "value": [],
            "confidence": 0.0
        }

    # De-duplicate by name + relationship
    unique = {}
    for a in associates:
        key = f"{a['name']}|{a['relationship']}"
        unique[key] = a

    associates = list(unique.values())

    confidence = score_attribute_confidence(
        attribute="associates",
        evidence=evidence
    )

    return {
        "value": associates if confidence >= 0.75 else [],
        "confidence": round(confidence, 2)
    }
