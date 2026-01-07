# agents/extractors/alias_extractor.py

from typing import List, Dict
import re

from agents.confidence.attribute_confidence import score_attribute_confidence


ALIAS_PATTERNS = [
    r"also known as\s+([A-Z][a-zA-Z\s]+)",
    r"\baka\s+([A-Z][a-zA-Z\s]+)",
    r"\balias\s+([A-Z][a-zA-Z\s]+)",
    r"\bknown as\s+([A-Z][a-zA-Z\s]+)"
]


ALLOWED_SOURCES = {
    "news",
    "official_registry",
    "wikidata"
}


def extract_aliases(
    subject_name: str,
    sources: List[Dict]
) -> Dict[str, object]:
    """
    Extract explicitly declared aliases only.
    No inferred nicknames.
    Returns normalized { value, confidence }.
    """

    aliases: List[Dict[str, str]] = []
    evidence: List[Dict[str, str]] = []

    for source in sources:
        text = source.get("text") or source.get("summary", "")
        source_type = source.get("source", "unknown")

        if not text or source_type not in ALLOWED_SOURCES:
            continue

        if subject_name.lower() not in text.lower():
            continue

        for pattern in ALIAS_PATTERNS:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)

            for match in matches:
                alias_name = match.strip()

                # Prevent self-aliasing
                if alias_name.lower() == subject_name.lower():
                    continue

                aliases.append({
                    "name": alias_name,
                    "source": source_type
                })

                evidence.append({
                    "value": alias_name,
                    "source": source_type
                })

    if not aliases:
        return {
            "value": [],
            "confidence": 0.0
        }

    # De-duplicate by alias name
    unique = {}
    for a in aliases:
        unique[a["name"]] = a

    aliases = list(unique.values())

    confidence = score_attribute_confidence(
        attribute="aliases",
        evidence=evidence
    )

    return {
        "value": aliases if confidence >= 0.60 else [],
        "confidence": round(confidence, 2)
    }
