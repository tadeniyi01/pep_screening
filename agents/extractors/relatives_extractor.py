# agents/extractors/relatives_extractor.py

import re
from typing import List, Dict

from agents.confidence.attribute_confidence import score_attribute_confidence


RELATION_PATTERNS = {
    "spouse": [
        r"(wife|husband|spouse)[:\s]+(?P<name>[A-Z][a-z]+(?:\s[A-Z][a-z]+)+)"
    ],
    "child": [
        r"(son|daughter|children)[:\s]+(?P<name>[A-Z][a-z]+(?:\s[A-Z][a-z]+)+)"
    ],
    "parent": [
        r"(father|mother)[:\s]+(?P<name>[A-Z][a-z]+(?:\s[A-Z][a-z]+)+)"
    ],
    "sibling": [
        r"(brother|sister)[:\s]+(?P<name>[A-Z][a-z]+(?:\s[A-Z][a-z]+)+)"
    ]
}


ALLOWED_SOURCES = {
    "news",
    "official_registry",
    "wikidata"
}


def extract_relatives(
    subject_name: str,
    sources: List[dict]
) -> Dict[str, object]:
    """
    Extract explicit, named family relationships from trusted sources only.
    Returns normalized { value, confidence } contract.
    """

    relatives: List[Dict[str, str]] = []
    evidence: List[Dict[str, str]] = []

    for src in sources:
        source_type = src.get("source")
        text = src.get("text", "")

        if source_type not in ALLOWED_SOURCES or not text:
            continue

        for relation, patterns in RELATION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if not match:
                    continue

                relative_name = match.group("name").strip()

                # Prevent self-reference / hallucination
                if relative_name.lower() == subject_name.lower():
                    continue

                relatives.append({
                    "name": relative_name,
                    "relationship": relation,
                    "source": source_type
                })

                evidence.append({
                    "value": f"{relation}:{relative_name}",
                    "source": source_type
                })

    if not relatives:
        return {
            "value": [],
            "confidence": 0.0
        }

    confidence = score_attribute_confidence(
        attribute="relatives",
        evidence=evidence
    )

    return {
        "value": relatives if confidence >= 0.75 else [],
        "confidence": round(confidence, 2)
    }
